"""
Progress Predictor ML service for game performance prediction.
"""
from typing import Dict, Optional, Tuple, Any
import logging
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib

from .data_extractor import extract_game_data, preprocess_features, extract_user_features

logger = logging.getLogger(__name__)


class ProgressPredictor:
    """
    Machine Learning model for predicting child's future game performance.
    
    Supports two model types:
    - 'linear': Linear Regression (faster, interpretable)
    - 'random_forest': Random Forest Regressor (more accurate, handles non-linearity)
    
    Features:
    - Training on historical game data
    - Predicting next score for specific user and game_type
    - Model persistence with joblib
    - Performance metrics tracking
    """
    
    FEATURE_COLUMNS = [
        'attempt_number',
        'avg_score',
        'std_score',
        'avg_duration',
        'total_hints',
        'score_trend',
        'last_score',
        'score_improvement',
        'days_since_start',
    ]
    
    def __init__(
        self,
        model_type: str = 'random_forest',
        model_dir: str = 'ml_models',
        window_size: int = 3,
    ):
        """
        Initialize the ProgressPredictor.
        
        Args:
            model_type: 'linear' or 'random_forest'
            model_dir: Directory to save/load models
            window_size: Number of past games to use for features
        """
        if model_type not in ['linear', 'random_forest']:
            raise ValueError("model_type must be 'linear' or 'random_forest'")
        
        self.model_type = model_type
        self.window_size = window_size
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize model
        if model_type == 'linear':
            self.model = LinearRegression()
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        
        # Feature scaler
        self.scaler = StandardScaler()
        
        # Training metrics
        self.metrics: Dict[str, float] = {}
        self.is_trained = False
        
        logger.info(
            f"Initialized ProgressPredictor with {model_type} model, "
            f"window_size={window_size}"
        )
    
    def train(
        self,
        game_type: Optional[str] = None,
        test_size: float = 0.2,
        min_entries: int = 5,
    ) -> Dict[str, float]:
        """
        Train the model on historical game data.
        
        Args:
            game_type: Specific game type to train on (None for all)
            test_size: Fraction of data to use for testing
            min_entries: Minimum entries per user-game combination
            
        Returns:
            Dictionary of performance metrics (MAE, RMSE, R²)
            
        Raises:
            ValueError: If insufficient training data
        """
        try:
            logger.info(f"Starting training for game_type={game_type}")
            
            # Extract and preprocess data
            df = extract_game_data(
                user_id=None,
                game_type=game_type,
                min_entries=min_entries,
            )
            
            X, y = preprocess_features(df, window_size=self.window_size)
            
            # Encode game_type if present
            if 'game_type' in X.columns:
                # Simple hash encoding for game types
                X['game_type'] = X['game_type'].apply(lambda x: hash(x) % 10000)
            
            # Select only numeric features
            X_features = X[self.FEATURE_COLUMNS].copy()
            
            # Handle any missing values
            X_features = X_features.fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_features,
                y,
                test_size=test_size,
                random_state=42,
            )
            
            logger.info(
                f"Training set: {len(X_train)} samples, "
                f"Test set: {len(X_test)} samples"
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            logger.info(f"Training {self.model_type} model...")
            self.model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred_train = self.model.predict(X_train_scaled)
            y_pred_test = self.model.predict(X_test_scaled)
            
            # Calculate metrics
            self.metrics = {
                'train_mae': mean_absolute_error(y_train, y_pred_train),
                'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'train_r2': r2_score(y_train, y_pred_train),
                'test_mae': mean_absolute_error(y_test, y_pred_test),
                'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'test_r2': r2_score(y_test, y_pred_test),
                'n_samples': len(X),
                'n_features': X_features.shape[1],
            }
            
            self.is_trained = True
            
            logger.info(
                f"Training complete. Test MAE: {self.metrics['test_mae']:.2f}, "
                f"Test RMSE: {self.metrics['test_rmse']:.2f}, "
                f"Test R²: {self.metrics['test_r2']:.3f}"
            )
            
            # Feature importance (for Random Forest)
            if self.model_type == 'random_forest':
                feature_importance = dict(zip(
                    self.FEATURE_COLUMNS,
                    self.model.feature_importances_
                ))
                logger.info(f"Feature importance: {feature_importance}")
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise
    
    def predict(
        self,
        user_id: int,
        game_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Predict next score and insights for a specific user and game type.
        
        Args:
            user_id: User ID
            game_type: Game type
            
        Returns:
            Dictionary with:
            - predicted_score: Predicted next score (0-100)
            - confidence: Confidence level (based on model performance)
            - insight: Human-readable insight string
            - days_to_mastery: Estimated days to reach mastery (score >= 90)
            - attempts_to_mastery: Estimated attempts to reach mastery
            
        Returns None if prediction cannot be made (insufficient data or untrained model)
        """
        if not self.is_trained:
            logger.warning("Model is not trained. Call train() first.")
            return None
        
        try:
            # Extract features for this user
            features = extract_user_features(
                user_id=user_id,
                game_type=game_type,
                window_size=self.window_size,
            )
            
            if features is None:
                return None
            
            # Prepare feature vector
            X_pred = pd.DataFrame([features])
            X_pred = X_pred[self.FEATURE_COLUMNS].fillna(0)
            
            # Scale features
            X_pred_scaled = self.scaler.transform(X_pred)
            
            # Make prediction
            predicted_score = float(self.model.predict(X_pred_scaled)[0])
            
            # Clip to valid score range
            predicted_score = np.clip(predicted_score, 0, 100)
            
            # Calculate confidence (inverse of test RMSE, normalized)
            confidence = max(0, min(100, 100 - self.metrics.get('test_rmse', 20)))
            
            # Generate insight
            insight = self._generate_insight(
                predicted_score=predicted_score,
                current_score=features['last_score'],
                score_trend=features['score_trend'],
                avg_score=features['avg_score'],
                game_type=game_type,
            )
            
            # Estimate mastery timeline
            mastery_threshold = 90
            days_to_mastery, attempts_to_mastery = self._estimate_mastery(
                current_score=features['last_score'],
                predicted_score=predicted_score,
                score_trend=features['score_trend'],
                days_since_start=features['days_since_start'],
                attempt_number=features['attempt_number'],
                mastery_threshold=mastery_threshold,
            )
            
            result = {
                'predicted_score': round(predicted_score, 1),
                'current_score': features['last_score'],
                'confidence': round(confidence, 1),
                'insight': insight,
                'days_to_mastery': days_to_mastery,
                'attempts_to_mastery': attempts_to_mastery,
                'score_trend': round(features['score_trend'], 2),
            }
            
            logger.info(
                f"Prediction for user {user_id}, game {game_type}: "
                f"score={predicted_score:.1f}, insight='{insight}'"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            return None
    
    def _generate_insight(
        self,
        predicted_score: float,
        current_score: float,
        score_trend: float,
        avg_score: float,
        game_type: str,
    ) -> str:
        """Generate human-readable insight from prediction in Ukrainian."""
        
        # Game type labels in Ukrainian
        game_labels = {
            'math': 'математиці',
            'memory': 'іграх на пам\'ять',
            'words': 'пазлах зі словами',
            'sound': 'іграх зі звуками',
            'sentences': 'побудові речень',
            'articulation': 'артикуляційній гімнастиці',
            'attention': 'іграх на увагу',
        }
        game_label = game_labels.get(game_type, 'цій грі')
        
        score_diff = predicted_score - current_score
        
        # Determine skill level and advice
        if predicted_score >= 90:
            level_text = "Чудовий результат! Дитина досягла майстерності"
            if score_trend > 0.5:
                advice = f"Продовжуйте підтримувати інтерес до {game_label}. Можна переходити до більш складних завдань."
            else:
                advice = f"Відмінний рівень у {game_label}! Можна використовувати як мотивацію для інших навичок."
        elif predicted_score >= 75:
            level_text = "Дуже добрий прогрес"
            if score_trend > 1.5:
                advice = f"Дитина активно покращується в {game_label}! Через кілька занять може досягти відмінних результатів."
            elif score_trend > 0.5:
                advice = f"Стабільне зростання в {game_label}. Рекомендується продовжити в такому ж темпі."
            else:
                advice = f"Хороший рівень у {game_label}, але є місце для росту. Додайте більше практики."
        elif predicted_score >= 60:
            level_text = "Помірний прогрес"
            if score_trend > 1:
                advice = f"Дитина напрацьовує навички в {game_label}. Підтримуйте регулярність занять!"
            elif score_trend > 0:
                advice = f"Повільне, але стабільне покращення в {game_label}. Варто трохи збільшити час практики."
            else:
                advice = f"Навички в {game_label} потребують уваги. Рекомендується додаткова практика та підтримка."
        else:
            level_text = "Розвиток навичок"
            if score_trend > 0.5:
                advice = f"Є позитивна динаміка в {game_label}! Продовжуйте роботу, результати обов'язково покращаться."
            elif score_trend >= 0:
                advice = f"Дитина потребує більше уваги до {game_label}. Спробуйте індивідуальний підхід та додаткову мотивацію."
            else:
                advice = f"Виникають труднощі в {game_label}. Варто переглянути методику та приділити більше часу базовим вправам."
        
        # Add emotional touch based on trend
        if score_trend > 2:
            emotion = "Блискучий прогрес! 🌟"
        elif score_trend > 1:
            emotion = "Відмінна динаміка! 📈"
        elif score_trend > 0.3:
            emotion = "Є покращення! ✅"
        elif score_trend > -0.3:
            emotion = "Стабільний рівень 📊"
        else:
            emotion = "Потрібна увага 💪"
        
        return f"{emotion} {level_text}. {advice}"
    
    def _estimate_mastery(
        self,
        current_score: float,
        predicted_score: float,
        score_trend: float,
        days_since_start: float,
        attempt_number: float,
        mastery_threshold: float = 90,
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Estimate days and attempts needed to reach mastery.
        
        Returns:
            Tuple of (days_to_mastery, attempts_to_mastery)
            None values indicate already at mastery or trend is negative
        """
        if current_score >= mastery_threshold:
            return (0, 0)
        
        if score_trend <= 0.1:
            # Not improving, hard to estimate
            return (None, None)
        
        # Estimate attempts needed
        score_gap = mastery_threshold - current_score
        attempts_needed = int(np.ceil(score_gap / score_trend))
        
        # Estimate days needed (based on current pace)
        if attempt_number > 1 and days_since_start > 0:
            days_per_attempt = days_since_start / (attempt_number - 1)
            days_needed = int(np.ceil(attempts_needed * days_per_attempt))
        else:
            days_needed = None
        
        return (days_needed, attempts_needed)
    
    def save(self, game_type: Optional[str] = None) -> Path:
        """
        Save trained model and scaler to disk.
        
        Args:
            game_type: Game type identifier for filename (optional)
            
        Returns:
            Path to saved model file
            
        Raises:
            ValueError: If model is not trained
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        # Create filename
        game_suffix = f"_{game_type}" if game_type else "_all"
        model_file = self.model_dir / f"progress_predictor_{self.model_type}{game_suffix}.joblib"
        scaler_file = self.model_dir / f"scaler_{self.model_type}{game_suffix}.joblib"
        metrics_file = self.model_dir / f"metrics_{self.model_type}{game_suffix}.json"
        
        # Save model, scaler, and metrics
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Model saved to {model_file}")
        
        return model_file
    
    def load(self, game_type: Optional[str] = None) -> bool:
        """
        Load trained model and scaler from disk.
        
        Args:
            game_type: Game type identifier for filename (optional)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Create filename
            game_suffix = f"_{game_type}" if game_type else "_all"
            model_file = self.model_dir / f"progress_predictor_{self.model_type}{game_suffix}.joblib"
            scaler_file = self.model_dir / f"scaler_{self.model_type}{game_suffix}.joblib"
            metrics_file = self.model_dir / f"metrics_{self.model_type}{game_suffix}.json"
            
            if not model_file.exists():
                logger.warning(f"Model file not found: {model_file}")
                return False
            
            # Load model and scaler
            self.model = joblib.load(model_file)
            self.scaler = joblib.load(scaler_file)
            
            # Load metrics if available
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    self.metrics = json.load(f)
            
            self.is_trained = True
            logger.info(f"Model loaded from {model_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model type, training status, and metrics
        """
        return {
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'window_size': self.window_size,
            'metrics': self.metrics,
            'feature_columns': self.FEATURE_COLUMNS,
        }
