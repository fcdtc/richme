"""
Data transformation utilities for multi-timeframe analysis
"""
import pandas as pd


def convert_to_weekly(daily_data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert daily OHLCV data to weekly OHLCV data.

    Since API does not provide weekly K-line, this function aggregates
    daily data into weekly bars: open=Monday open, high=weekly max,
    low=weekly min, close=Friday close, volume=weekly sum.

    Args:
        daily_data: DataFrame with columns [date, open, high, low, close, volume]

    Returns:
        Weekly DataFrame with same structure
    """
    if daily_data.empty:
        return daily_data.copy()

    df = daily_data.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Group by week (ISO week number)
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.isocalendar().year

    # Aggregate: open=first, high=max, low=min, close=last, volume=sum
    weekly = df.groupby(['year', 'week']).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index()

    # Recalculate date as Friday of each week
    def get_friday_of_week(row):
        year = int(row['year'])
        week = int(row['week'])
        return pd.to_datetime(f"{year}-W{week}-5", format="%Y-W%W-%w")

    weekly['date'] = weekly.apply(get_friday_of_week, axis=1)
    weekly = weekly.drop(columns=['year', 'week'])

    # Ensure minimum 26 weeks for weekly indicators
    return weekly


def validate_weekly_data(weekly_data: pd.DataFrame, min_weeks: int = 10) -> bool:
    """
    Validate if we have sufficient weekly data for analysis.

    Args:
        weekly_data: Weekly DataFrame
        min_weeks: Minimum required weeks (reduced to 10 for flexibility)

    Returns:
        True if sufficient, False otherwise
    """
    return len(weekly_data) >= min_weeks
