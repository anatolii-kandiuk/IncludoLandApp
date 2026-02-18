"""
Data extraction and preprocessing utilities for ML models.
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import timedelta

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q

from accounts.models import GameResult

User = get_user_model()
logger = logging.getLogger(__name__)


def extract_game_data(
    user_id: Optional[int] = None,
    game_type: Optional[str] = None,
    min_entries: int = 5,
) -> pd.DataFrame:
    """
    Extract historical GameResult data for training or prediction.
    
    Args:
        user_id: User ID to filter by (None for all users)
        game_type: Game type to filter by (None for all game types)
        min_entries: Minimum number of entries required per user-game combination
        
    Returns:
        DataFrame with columns: user_id, game_type, score, duration_seconds,
        hints_used, attempts, created_at
        
    Raises:
        ValueError: If insufficient data is available
    """
    try:
        # Build query with optimized select_related and filters
        queryset: QuerySet[GameResult] = GameResult.objects.select_related('user')
        
        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)
        
        if game_type is not None:
            queryset = queryset.filter(game_type=game_type)
        
        # Order by user and creation time for sequential analysis
        queryset = queryset.order_by('user_id', 'game_type', 'created_at')
        
        # Extract data into a list of dictionaries
        data: List[Dict[str, Any]] = []
        
        for result in queryset:
            details: Dict[str, Any] = result.details or {}
            
            data.append({
                'user_id': result.user_id,
                'game_type': result.game_type,
                'score': result.score,
                'duration_seconds': result.duration_seconds or 0,
                'hints_used': details.get('hints_used', 0),
                'attempts': details.get('attempts', 1),
                'created_at': result.created_at,
            })
        
        if not data:
            logger.warning(
                f"No game results found for user_id={user_id}, game_type={game_type}"
            )
            raise ValueError("Insufficient data: no game results found")
        
        df = pd.DataFrame(data)
        
        # Filter out user-game combinations with insufficient data
        if min_entries > 1:
            group_counts = df.groupby(['user_id', 'game_type']).size()
            valid_groups = group_counts[group_counts >= min_entries].index
            
            if len(valid_groups) == 0:
                raise ValueError(
                    f"Insufficient data: minimum {min_entries} entries per user-game required"
                )
            
            df = df.set_index(['user_id', 'game_type'])
            df = df.loc[df.index.isin(valid_groups)]
            df = df.reset_index()
        
        logger.info(
            f"Extracted {len(df)} game results for {df['user_id'].nunique()} users"
        )
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting game data: {str(e)}")
        raise


def preprocess_features(
    df: pd.DataFrame,
    window_size: int = 3,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Engineer features from raw game data for training.
    
    Creates features like:
    - Moving average of last N scores
    - Average duration
    - Total hints used in last N games
    - Attempt number (sequence position)
    - Days since first attempt
    - Score trend (slope)
    
    Args:
        df: DataFrame from extract_game_data()
        window_size: Number of past games to include in rolling features
        
    Returns:
        Tuple of (X features DataFrame, y target Series)
        Target is the score of the next attempt
        
    Raises:
        ValueError: If dataframe is too small or missing required columns
    """
    required_cols = [
        'user_id', 'game_type', 'score', 'duration_seconds',
        'hints_used', 'attempts', 'created_at'
    ]
    
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if len(df) < window_size + 1:
        raise ValueError(
            f"Insufficient data: need at least {window_size + 1} entries, got {len(df)}"
        )
    
    # Sort by user, game_type, and time
    df = df.sort_values(['user_id', 'game_type', 'created_at']).reset_index(drop=True)
    
    # Create features
    features_list: List[Dict[str, Any]] = []
    targets: List[float] = []
    
    # Group by user and game type
    for (user_id, game_type), group in df.groupby(['user_id', 'game_type']):
        group = group.reset_index(drop=True)
        
        # Need at least window_size + 1 entries to create features and target
        if len(group) < window_size + 1:
            continue
        
        # Calculate days since first attempt
        first_date = group['created_at'].iloc[0]
        group['days_since_start'] = (
            group['created_at'] - first_date
        ).dt.total_seconds() / 86400
        
        # For each possible prediction point
        for i in range(window_size, len(group)):
            window_data = group.iloc[i - window_size:i]
            
            # Calculate rolling features
            avg_score = window_data['score'].mean()
            std_score = window_data['score'].std() if len(window_data) > 1 else 0
            avg_duration = window_data['duration_seconds'].mean()
            total_hints = window_data['hints_used'].sum()
            
            # Calculate score trend (linear regression slope)
            if len(window_data) > 1:
                x = np.arange(len(window_data))
                y = window_data['score'].values
                slope = np.polyfit(x, y, 1)[0]
            else:
                slope = 0
            
            # Last score and improvement from previous
            last_score = window_data['score'].iloc[-1]
            if len(window_data) > 1:
                prev_score = window_data['score'].iloc[-2]
                score_improvement = last_score - prev_score
            else:
                score_improvement = 0
            
            # Current attempt number
            attempt_number = i + 1
            
            # Days since start
            days_since_start = group['days_since_start'].iloc[i - 1]
            
            # Target: next score
            next_score = group['score'].iloc[i]
            
            features_list.append({
                'user_id': user_id,
                'game_type': game_type,
                'attempt_number': attempt_number,
                'avg_score': avg_score,
                'std_score': std_score,
                'avg_duration': avg_duration,
                'total_hints': total_hints,
                'score_trend': slope,
                'last_score': last_score,
                'score_improvement': score_improvement,
                'days_since_start': days_since_start,
            })
            
            targets.append(next_score)
    
    if not features_list:
        raise ValueError(
            f"Could not generate features: need at least {window_size + 1} "
            "sequential entries per user-game combination"
        )
    
    X = pd.DataFrame(features_list)
    y = pd.Series(targets, name='next_score')
    
    logger.info(f"Generated {len(X)} training samples with {X.shape[1]} features")
    
    return X, y


def extract_user_features(
    user_id: int,
    game_type: str,
    window_size: int = 3,
) -> Optional[Dict[str, float]]:
    """
    Extract features for a specific user and game type for prediction.
    
    Args:
        user_id: User ID
        game_type: Game type
        window_size: Number of past games to include
        
    Returns:
        Dictionary of features, or None if insufficient data
    """
    try:
        df = extract_game_data(user_id=user_id, game_type=game_type, min_entries=window_size)
        
        if len(df) < window_size:
            logger.warning(
                f"Insufficient data for user {user_id}, game {game_type}: "
                f"need {window_size}, got {len(df)}"
            )
            return None
        
        # Sort by time and take last N entries
        df = df.sort_values('created_at').tail(window_size)
        
        # Calculate features
        avg_score = df['score'].mean()
        std_score = df['score'].std() if len(df) > 1 else 0
        avg_duration = df['duration_seconds'].mean()
        total_hints = df['hints_used'].sum()
        
        # Calculate trend
        if len(df) > 1:
            x = np.arange(len(df))
            y = df['score'].values
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0
        
        last_score = df['score'].iloc[-1]
        if len(df) > 1:
            prev_score = df['score'].iloc[-2]
            score_improvement = last_score - prev_score
        else:
            score_improvement = 0
        
        # Days since first attempt
        first_date = df['created_at'].iloc[0]
        last_date = df['created_at'].iloc[-1]
        days_since_start = (last_date - first_date).total_seconds() / 86400
        
        attempt_number = len(df) + 1
        
        features = {
            'user_id': float(user_id),
            'game_type': float(hash(game_type) % 10000),  # Simple encoding
            'attempt_number': float(attempt_number),
            'avg_score': float(avg_score),
            'std_score': float(std_score),
            'avg_duration': float(avg_duration),
            'total_hints': float(total_hints),
            'score_trend': float(slope),
            'last_score': float(last_score),
            'score_improvement': float(score_improvement),
            'days_since_start': float(days_since_start),
        }
        
        return features
        
    except Exception as e:
        logger.error(
            f"Error extracting features for user {user_id}, game {game_type}: {str(e)}"
        )
        return None
