"""
ML service for predicting game performance.
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
    ML model for predicting child's future game performance.
    
    Supports two model types:
    - 'linear': Linear Regression (faster, interpretable)
    - 'random_forest': Random Forest Regressor (more accurate, handles non-linearity)
    
    Features:
    - Training on historical game data
    - Predicting next score for a specific user and game_type
    - Model persistence with joblib
    - Performance metrics tracking
    """
    
    FEATURE_COLUMNS = [
        'attempt_number',
        'avg_score',
        'std_score',
        'avg_duration',
        'total_hints',
        'avg_successful_attempts',
        'avg_failed_attempts',
        'failed_attempts_trend',
        'avg_max_streak',
        'time_of_day',
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
            
            # Handle missing values
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

            # Prevent sharp drop when current score is high and trend is positive
            if features['last_score'] >= 90 and features['score_trend'] > 0:
                predicted_score = max(predicted_score, features['last_score'] - 15)
            
            # Calculate confidence based on model type
            if self.model_type == 'random_forest' and hasattr(self.model, 'estimators_'):
                tree_predictions = [
                    estimator.predict(X_pred_scaled)[0]
                    for estimator in self.model.estimators_
                ]
                prediction_std = float(np.std(tree_predictions)) if len(tree_predictions) > 1 else 0.0
                confidence = max(0, min(100, 100 - (prediction_std * 2)))
            else:
                confidence = max(0, min(100, 100 - self.metrics.get('test_rmse', 20)))
            
            # Generate insight
            insight = self._generate_insight(
                predicted_score=predicted_score,
                current_score=features['last_score'],
                score_trend=features['score_trend'],
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
                f"score={predicted_score:.1f}, insight_generated=True"
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
        game_type: str,
    ) -> str:
        """
        Generate a specialist insight based on model output.
        The logic considers absolute score, historical trend, and expected deviation.
        """

        # Dictionary with proper Ukrainian cases for activity labels
        game_labels = {
            'math': 'математиці',
            'memory': 'іграх на пам\'ять',
            'words': 'пазлах зі словами',
            'sound': 'іграх зі звуками',
            'sentences': 'побудові речень',
            'articulation': 'артикуляційній гімнастиці',
            'attention': 'вправах на увагу',
        }
        game_label = game_labels.get(game_type, 'цій активності')

        # Delta: difference between predicted and current score.
        # delta > 0 means expected improvement, delta < 0 means expected decline.
        delta = predicted_score - current_score

        # === Level 1: Mastery (90-100) ===
        if predicted_score >= 90:
            status = 'Рівень майстерності.'

            if delta < -5:
                advice = (
                    f'Попри високі результати, прогнозується зниження ефективності у {game_label}. '
                    f'Ймовірно, дитина відчуває втому або втрачає інтерес до одноманітних завдань. '
                    f'Рекомендується зробити перерву або змінити тип активності.'
                )
            elif current_score >= 95 and delta >= 0:
                # Absolute top performance
                advice = (
                    f'Навичка у {game_label} засвоєна на відмінно. '
                    f'Для підтримки нейропластичності варто переходити до значно складніших завдань '
                    f"або використовувати цю гру як 'бонус' для мотивації."
                )
            elif score_trend > 0.5:
                # Stable growth at high performance level
                advice = (
                    f'Спостерігається стійка позитивна динаміка. Дитина впевнено закріплює матеріал. '
                    f'Можна сміливо підвищувати рівень складності.'
                )
            else:
                # Stable high plateau
                advice = (
                    f'Результати стабільно високі. Рекомендується періодична практика у {game_label} '
                    f'для профілактики забування, але основний акцент варто змістити на інші навички.'
                )

        # === Level 2: Confident skill (75-89) ===
        elif predicted_score >= 75:
            status = 'Впевнене володіння навичкою.'

            if score_trend > 2.0:
                # Sharp upward jump
                advice = (
                    f'Зафіксовано стрімкий прогрес у {game_label}! Дитина увійшла в стан потоку. '
                    f'Важливо підтримати цей імпульс похвалою та не переривати серію занять.'
                )
            elif delta > 5:
                # Model expects meaningful improvement
                advice = (
                    f'Аналіз показує високий потенціал до росту. У наступних спробах очікується покращення результатів. '
                    f'Продовжуйте заняття в поточному темпі.'
                )
            elif delta < -10:
                # Model expects sharp decline
                advice = (
                    f'Увага: модель прогнозує суттєвий спад результативності. '
                    f'Можливо, завдання стало занадто складним або нудним. Спробуйте спростити умови.'
                )
            else:
                # Slow, steady progress
                advice = (
                    f'Хороший робочий рівень у {game_label}. Є простір для вдосконалення швидкості реакції. '
                    f'Рекомендується регулярна практика.'
                )

        # === Level 3: Skill formation (60-74) ===
        elif predicted_score >= 60:
            status = 'Етап активного формування навички.'

            if score_trend > 1.5 and delta > 0:
                advice = (
                    f'Позитивний зсув у {game_label}. Дитина починає розуміти алгоритм виконання. '
                    f'Зараз критично важливо не підвищувати складність, щоб закріпити успіх.'
                )
            elif score_trend < -1.0:
                advice = (
                    f'Спостерігається негативна динаміка. Дитина може відчувати фрустрацію. '
                    f'Варто збільшити кількість підказок або повернутися на крок назад.'
                )
            elif delta < 0:
                advice = (
                    f'Результати у {game_label} нестабільні. Прогнозується коливання ефективності. '
                    f'Потребує додаткового контролю з боку спеціаліста.'
                )
            else:
                advice = (
                    f'Помірний прогрес. Дитина виконує завдання, але потребує більше часу на обдумування. '
                    f'Не підганяйте учня, дайте можливість працювати у власному темпі.'
                )

        # === Level 4: Entry level / difficulties (<60) ===
        else:
            status = 'Потребує посиленої уваги.'

            if delta > 10:
                # Low score but optimistic breakthrough prediction
                advice = (
                    f'Модель прогнозує значний прорив у {game_label}! '
                    f"Схоже, дитина нарешті зрозуміла принцип завдання. Обов'язково підтримайте ці спроби."
                )
            elif score_trend > 0:
                advice = (
                    f'Є перші ознаки покращення, але навичка у {game_label} ще не сформована. '
                    f'Рекомендується використання наочних матеріалів та спільне виконання завдань.'
                )
            elif score_trend < 0 and current_score < 30:
                advice = (
                    f'Критично низькі показники. Дитина не справляється із завданням у {game_label}. '
                    f'Необхідно змінити методику навчання або тимчасово виключити цю вправу.'
                )
            else:
                advice = (
                    f'Виникають систематичні труднощі. Рекомендується розбити завдання на простіші етапи '
                    f'та збільшити частоту коротких сесій.'
                )

        return f'{status} {advice}'
    
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

            expected_features = len(self.FEATURE_COLUMNS)
            scaler_features = getattr(self.scaler, 'n_features_in_', None)
            if scaler_features is not None and int(scaler_features) != expected_features:
                logger.warning(
                    "Loaded scaler expects %s features, but current schema has %s. "
                    "Model will be treated as outdated.",
                    scaler_features,
                    expected_features,
                )
                return False
            
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
