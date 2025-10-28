"""
Utility functions for AQI Prediction Project
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_aqi_category(aqi):
    """
    Return AQI category, color, and health message based on AQI value
    
    Args:
        aqi (float): Air Quality Index value
        
    Returns:
        dict: Category information including name, color, and health message
    """
    if pd.isna(aqi):
        return {
            'category': 'Unknown',
            'color': '#808080',
            'health_message': 'Data not available'
        }
    
    if aqi <= 50:
        return {
            'category': 'Good',
            'color': '#00E400',
            'health_message': 'Air quality is satisfactory, and air pollution poses little or no risk.'
        }
    elif aqi <= 100:
        return {
            'category': 'Moderate',
            'color': '#FFFF00',
            'health_message': 'Air quality is acceptable. However, there may be a risk for some people.'
        }
    elif aqi <= 150:
        return {
            'category': 'Unhealthy for Sensitive Groups',
            'color': '#FF7E00',
            'health_message': 'Members of sensitive groups may experience health effects.'
        }
    elif aqi <= 200:
        return {
            'category': 'Unhealthy',
            'color': '#FF0000',
            'health_message': 'Some members of the general public may experience health effects.'
        }
    elif aqi <= 300:
        return {
            'category': 'Very Unhealthy',
            'color': '#8F3F97',
            'health_message': 'Health alert: The risk of health effects is increased for everyone.'
        }
    else:
        return {
            'category': 'Hazardous',
            'color': '#7E0023',
            'health_message': 'Health warning of emergency conditions: everyone is more likely to be affected.'
        }

def create_time_features(timestamp):
    """
    Create time-based features from timestamp
    
    Args:
        timestamp (datetime): Datetime object
        
    Returns:
        dict: Time-based features
    """
    return {
        'hour': timestamp.hour,
        'day_of_week': timestamp.weekday(),
        'day_of_month': timestamp.day,
        'month': timestamp.month,
        'year': timestamp.year,
        'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
        'is_rush_hour': 1 if timestamp.hour in [7, 8, 9, 17, 18, 19] else 0,
        'season': get_season(timestamp.month),
        'hour_sin': np.sin(2 * np.pi * timestamp.hour / 24),
        'hour_cos': np.cos(2 * np.pi * timestamp.hour / 24),
        'month_sin': np.sin(2 * np.pi * timestamp.month / 12),
        'month_cos': np.cos(2 * np.pi * timestamp.month / 12)
    }

def get_season(month):
    """
    Get season based on month (for Northern Hemisphere)
    
    Args:
        month (int): Month number (1-12)
        
    Returns:
        int: Season code (0-3)
    """
    if month in [12, 1, 2]:
        return 0  # Winter
    elif month in [3, 4, 5]:
        return 1  # Spring
    elif month in [6, 7, 8]:
        return 2  # Summer
    else:
        return 3  # Fall

def handle_missing_values(df, method='interpolate'):
    """
    Handle missing values in the dataframe
    
    Args:
        df (pd.DataFrame): Input dataframe
        method (str): Method to handle missing values ('interpolate', 'forward_fill', 'drop')
        
    Returns:
        pd.DataFrame: Dataframe with handled missing values
    """
    if method == 'interpolate':
        # Interpolate numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit_direction='both')
    elif method == 'forward_fill':
        df = df.fillna(method='ffill').fillna(method='bfill')
    elif method == 'drop':
        df = df.dropna()
    
    return df

def calculate_lagged_features(df, column='aqi', lags=[1, 3, 6, 12, 24]):
    """
    Calculate lagged features for time series prediction
    
    Args:
        df (pd.DataFrame): Input dataframe
        column (str): Column name to create lags for
        lags (list): List of lag periods
        
    Returns:
        pd.DataFrame: Dataframe with lagged features
    """
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    for lag in lags:
        df[f'{column}_lag_{lag}h'] = df[column].shift(lag)
    
    return df

def calculate_rolling_features(df, column='aqi', windows=[3, 6, 12, 24]):
    """
    Calculate rolling statistics for time series features
    
    Args:
        df (pd.DataFrame): Input dataframe
        column (str): Column name to calculate rolling stats for
        windows (list): List of window sizes
        
    Returns:
        pd.DataFrame: Dataframe with rolling features
    """
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    for window in windows:
        df[f'{column}_rolling_mean_{window}h'] = df[column].rolling(
            window=window, min_periods=1
        ).mean()
        df[f'{column}_rolling_std_{window}h'] = df[column].rolling(
            window=window, min_periods=1
        ).std()
        df[f'{column}_rolling_min_{window}h'] = df[column].rolling(
            window=window, min_periods=1
        ).min()
        df[f'{column}_rolling_max_{window}h'] = df[column].rolling(
            window=window, min_periods=1
        ).max()
    
    return df

def calculate_change_features(df, column='aqi'):
    """
    Calculate change and rate of change features
    
    Args:
        df (pd.DataFrame): Input dataframe
        column (str): Column name to calculate changes for
        
    Returns:
        pd.DataFrame: Dataframe with change features
    """
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    df[f'{column}_change'] = df[column].diff()
    df[f'{column}_change_rate'] = df[column].pct_change()
    df[f'{column}_change_3h'] = df[column].diff(3)
    df[f'{column}_change_24h'] = df[column].diff(24)
    
    return df

def validate_data(df, required_columns):
    """
    Validate that dataframe has required columns and data
    
    Args:
        df (pd.DataFrame): Input dataframe
        required_columns (list): List of required column names
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if df is None or len(df) == 0:
        return False, "Dataframe is empty or None"
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"
    
    return True, "Data is valid"

def get_env_variable(key, default=None, required=True):
    """
    Get environment variable with validation
    
    Args:
        key (str): Environment variable key
        default: Default value if not found
        required (bool): Whether the variable is required
        
    Returns:
        str: Environment variable value
        
    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)
    
    if required and not value:
        raise ValueError(
            f"Required environment variable '{key}' not found. "
            f"Please set it in your .env file."
        )
    
    return value

def save_dataframe(df, filename, directory='data'):
    """
    Save dataframe to CSV file
    
    Args:
        df (pd.DataFrame): Dataframe to save
        filename (str): Output filename
        directory (str): Output directory
    """
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(df)} rows to {filepath}")

def load_dataframe(filename, directory='data'):
    """
    Load dataframe from CSV file
    
    Args:
        filename (str): Input filename
        directory (str): Input directory
        
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    print(f"Loaded {len(df)} rows from {filepath}")
    return df

def print_data_summary(df):
    """
    Print summary statistics of the dataframe
    
    Args:
        df (pd.DataFrame): Input dataframe
    """
    print("\n" + "="*50)
    print("DATA SUMMARY")
    print("="*50)
    print(f"Shape: {df.shape}")
    print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"\nMissing Values:")
    print(df.isnull().sum())
    print(f"\nNumeric Columns Summary:")
    print(df.describe())
    print("="*50 + "\n")