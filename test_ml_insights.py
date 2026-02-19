#!/usr/bin/env python
"""
Test script to verify ML predictions work correctly.
Run this after setting up the Django environment.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'includoland.settings')
django.setup()

from ml_services import ProgressPredictor


def test_insight_generation():
    """Test that Ukrainian insights are generated correctly"""
    print("=" * 60)
    print("Testing Ukrainian Insight Generation")
    print("=" * 60)
    
    predictor = ProgressPredictor(model_type='random_forest')
    
    # Test different scenarios
    test_cases = [
        {
            'name': 'Excellent progress in math',
            'predicted_score': 95.0,
            'current_score': 90.0,
            'score_trend': 2.5,
            'avg_score': 88.0,
            'game_type': 'math',
        },
        {
            'name': 'Good progress in articulation',
            'predicted_score': 78.0,
            'current_score': 72.0,
            'score_trend': 1.2,
            'avg_score': 70.0,
            'game_type': 'articulation',
        },
        {
            'name': 'Needs attention in memory',
            'predicted_score': 52.0,
            'current_score': 50.0,
            'score_trend': 0.3,
            'avg_score': 48.0,
            'game_type': 'memory',
        },
        {
            'name': 'Struggling with words',
            'predicted_score': 42.0,
            'current_score': 45.0,
            'score_trend': -0.8,
            'avg_score': 43.0,
            'game_type': 'words',
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 60)
        
        insight = predictor._generate_insight(
            predicted_score=test['predicted_score'],
            current_score=test['current_score'],
            score_trend=test['score_trend'],
            avg_score=test['avg_score'],
            game_type=test['game_type'],
        )
        
        print(f"Game Type: {test['game_type']}")
        print(f"Current Score: {test['current_score']}")
        print(f"Predicted Score: {test['predicted_score']}")
        print(f"Trend: {test['score_trend']:+.1f}")
        print(f"\n💬 Insight (Ukrainian):")
        print(f"   {insight}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    test_insight_generation()
