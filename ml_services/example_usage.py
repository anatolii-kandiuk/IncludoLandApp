"""
Example script demonstrating ML service usage.

This script shows how to:
1. Train a model
2. Make predictions
3. Save and load models
4. Extract and analyze features

Run this after collecting sufficient game data:
    python -m ml_services.example_usage
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'includoland.settings')
import django
django.setup()

from ml_services import ProgressPredictor, extract_game_data, preprocess_features
from accounts.models import GameResult, User


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def example_data_extraction():
    """Example 1: Extract and explore game data."""
    print_section("Example 1: Data Extraction")
    
    try:
        # Extract all math game data
        df = extract_game_data(game_type='math', min_entries=3)
        
        print(f"Extracted {len(df)} game results")
        print(f"Users: {df['user_id'].nunique()}")
        print(f"Date range: {df['created_at'].min()} to {df['created_at'].max()}")
        print(f"\nScore statistics:")
        print(df['score'].describe())
        
        # Show sample
        print(f"\nSample data (first 5 rows):")
        print(df.head())
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure you have sufficient game data in the database.")


def example_feature_engineering():
    """Example 2: Feature engineering."""
    print_section("Example 2: Feature Engineering")
    
    try:
        # Extract data
        df = extract_game_data(game_type='memory', min_entries=5)
        
        # Preprocess into features
        X, y = preprocess_features(df, window_size=3)
        
        print(f"Generated {len(X)} training samples")
        print(f"Features: {X.shape[1]}")
        print(f"\nFeature columns:")
        for col in X.columns:
            print(f"  - {col}")
        
        print(f"\nFeature statistics:")
        print(X.describe())
        
        print(f"\nTarget (next score) statistics:")
        print(y.describe())
        
    except ValueError as e:
        print(f"Error: {e}")


def example_training():
    """Example 3: Train a model."""
    print_section("Example 3: Model Training")
    
    try:
        # Initialize predictor with Random Forest
        predictor = ProgressPredictor(
            model_type='random_forest',
            model_dir='ml_models',
            window_size=3,
        )
        
        print("Training model on 'math' game type...")
        metrics = predictor.train(
            game_type='math',
            test_size=0.2,
            min_entries=5,
        )
        
        print("\n✓ Training complete!")
        print(f"\nPerformance Metrics:")
        print(f"  Training MAE:   {metrics['train_mae']:.2f}")
        print(f"  Training RMSE:  {metrics['train_rmse']:.2f}")
        print(f"  Training R²:    {metrics['train_r2']:.3f}")
        print(f"  Test MAE:       {metrics['test_mae']:.2f}")
        print(f"  Test RMSE:      {metrics['test_rmse']:.2f}")
        print(f"  Test R²:        {metrics['test_r2']:.3f}")
        print(f"  Samples:        {int(metrics['n_samples'])}")
        print(f"  Features:       {int(metrics['n_features'])}")
        
        # Save model
        model_path = predictor.save(game_type='math')
        print(f"\n✓ Model saved to: {model_path}")
        
        return predictor
        
    except ValueError as e:
        print(f"Error: {e}")
        return None


def example_prediction(predictor=None):
    """Example 4: Make predictions."""
    print_section("Example 4: Making Predictions")
    
    # Load model if not provided
    if predictor is None:
        predictor = ProgressPredictor(
            model_type='random_forest',
            model_dir='ml_models',
            window_size=3,
        )
        
        if not predictor.load(game_type='math'):
            print("Error: No trained model found. Train a model first.")
            return
        
        print("✓ Model loaded")
    
    # Get a sample user who has played math games
    try:
        sample_result = GameResult.objects.filter(
            game_type='math'
        ).select_related('user').first()
        
        if not sample_result:
            print("No math game results found in database.")
            return
        
        user_id = sample_result.user_id
        print(f"\nMaking prediction for user_id={user_id}, game_type='math'...")
        
        # Make prediction
        result = predictor.predict(user_id=user_id, game_type='math')
        
        if result is None:
            print(f"Cannot make prediction - insufficient data for this user.")
            return
        
        print("\n✓ Prediction complete!")
        print(f"\nResults:")
        print(f"  Current Score:      {result['current_score']:.1f}")
        print(f"  Predicted Score:    {result['predicted_score']:.1f}")
        print(f"  Confidence:         {result['confidence']:.1f}%")
        print(f"  Score Trend:        {result['score_trend']:.2f} points/game")
        print(f"  Days to Mastery:    {result['days_to_mastery'] or 'N/A'}")
        print(f"  Attempts to Mastery: {result['attempts_to_mastery'] or 'N/A'}")
        print(f"\n  Insight: {result['insight']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def example_model_comparison():
    """Example 5: Compare Linear vs Random Forest."""
    print_section("Example 5: Model Comparison")
    
    models = ['linear', 'random_forest']
    results = {}
    
    for model_type in models:
        try:
            print(f"\nTraining {model_type} model...")
            
            predictor = ProgressPredictor(
                model_type=model_type,
                model_dir='ml_models',
                window_size=3,
            )
            
            metrics = predictor.train(
                game_type='math',
                test_size=0.2,
                min_entries=5,
            )
            
            results[model_type] = metrics
            print(f"  Test MAE: {metrics['test_mae']:.2f}, Test R²: {metrics['test_r2']:.3f}")
            
        except ValueError as e:
            print(f"  Error: {e}")
    
    if len(results) == 2:
        print("\n" + "-" * 60)
        print("Comparison:")
        print(f"  Linear MAE:        {results['linear']['test_mae']:.2f}")
        print(f"  Random Forest MAE: {results['random_forest']['test_mae']:.2f}")
        print(f"  Linear R²:         {results['linear']['test_r2']:.3f}")
        print(f"  Random Forest R²:  {results['random_forest']['test_r2']:.3f}")
        
        if results['random_forest']['test_mae'] < results['linear']['test_mae']:
            print("\n  Winner: Random Forest (lower error)")
        else:
            print("\n  Winner: Linear (lower error)")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  ML Service Usage Examples")
    print("#" * 60)
    
    # Check if we have any game data
    game_count = GameResult.objects.count()
    user_count = User.objects.count()
    
    print(f"\nDatabase Status:")
    print(f"  Total game results: {game_count}")
    print(f"  Total users: {user_count}")
    
    if game_count == 0:
        print("\n⚠ Warning: No game results in database!")
        print("Please add some game data before running examples.")
        return
    
    # Run examples
    try:
        example_data_extraction()
        example_feature_engineering()
        predictor = example_training()
        if predictor:
            example_prediction(predictor)
        # example_model_comparison()  # Uncomment to compare models
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "#" * 60)
    print("#  Examples Complete")
    print("#" * 60 + "\n")


if __name__ == '__main__':
    main()
