"""
Create Synthetic AQI Data for Testing
This generates realistic-looking data with variation over time
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hopsworks
import os
from dotenv import load_dotenv

load_dotenv()

def create_synthetic_aqi_data(days=7):
    """
    Create synthetic but realistic AQI data
    
    Args:
        days (int): Number of days of data to create
        
    Returns:
        pd.DataFrame: Synthetic data
    """
    print(f"Creating {days} days of synthetic data...")
    
    # Start from 7 days ago
    start_time = datetime.now() - timedelta(days=days)
    
    # Create hourly timestamps
    timestamps = [start_time + timedelta(hours=i) for i in range(days * 24)]
    
    data = []
    base_aqi = 100  # Base AQI value
    
    for i, ts in enumerate(timestamps):
        # Add daily and hourly patterns
        hour_effect = 20 * np.sin(2 * np.pi * ts.hour / 24)  # Daily cycle
        day_effect = 15 * np.sin(2 * np.pi * ts.day / 30)  # Monthly cycle
        
        # Add random noise
        noise = np.random.normal(0, 10)
        
        # Calculate AQI with variation
        aqi = base_aqi + hour_effect + day_effect + noise
        aqi = max(10, min(300, aqi))  # Clamp between 10 and 300
        
        # Convert to OpenWeather scale (1-5)
        if aqi <= 50:
            aqi_ow = 1
        elif aqi <= 100:
            aqi_ow = 2
        elif aqi <= 150:
            aqi_ow = 3
        elif aqi <= 200:
            aqi_ow = 4
        else:
            aqi_ow = 5
        
        # Generate correlated pollutant values
        pm25 = aqi * 0.4 + np.random.normal(0, 5)
        pm10 = pm25 * 2.0 + np.random.normal(0, 10)
        
        # Weather features with patterns
        temp = 25 + 5 * np.sin(2 * np.pi * ts.hour / 24) + np.random.normal(0, 2)
        humidity = 50 + 20 * np.sin(2 * np.pi * (ts.hour + 6) / 24) + np.random.normal(0, 5)
        
        record = {
            'timestamp': ts,
            'city': 'karachi',
            'aqi': aqi,
            'aqi_openweather': aqi_ow,
            'pm25': max(0, pm25),
            'pm10': max(0, pm10),
            'o3': np.random.uniform(20, 100),
            'no2': np.random.uniform(10, 80),
            'so2': np.random.uniform(5, 50),
            'co': np.random.uniform(200, 800),
            'no': np.random.uniform(5, 30),
            'nh3': np.random.uniform(1, 20),
            'temperature': temp,
            'feels_like': temp + np.random.uniform(-2, 2),
            'humidity': max(0, min(100, humidity)),
            'pressure': 1013 + np.random.uniform(-10, 10),
            'wind_speed': abs(np.random.normal(3, 2)),
            'wind_deg': np.random.uniform(0, 360),
            'clouds': np.random.uniform(0, 100),
            'latitude': 24.8607,
            'longitude': 67.0011,
            'hour': ts.hour,
            'day_of_week': ts.weekday(),
            'day_of_month': ts.day,
            'month': ts.month,
            'year': ts.year,
            'is_weekend': 1 if ts.weekday() >= 5 else 0,
            'is_rush_hour': 1 if ts.hour in [7, 8, 9, 17, 18, 19] else 0,
            'season': (ts.month % 12) // 3,
            'hour_sin': np.sin(2 * np.pi * ts.hour / 24),
            'hour_cos': np.cos(2 * np.pi * ts.hour / 24),
            'month_sin': np.sin(2 * np.pi * ts.month / 12),
            'month_cos': np.cos(2 * np.pi * ts.month / 12)
        }
        
        data.append(record)
    
    df = pd.DataFrame(data)
    print(f"✓ Created {len(df)} synthetic records")
    
    # Add some statistics
    print(f"\nData Statistics:")
    print(f"  AQI Range: {df['aqi'].min():.1f} - {df['aqi'].max():.1f}")
    print(f"  AQI Mean: {df['aqi'].mean():.1f}")
    print(f"  PM2.5 Mean: {df['pm25'].mean():.1f}")
    print(f"  Temperature Range: {df['temperature'].min():.1f}°C - {df['temperature'].max():.1f}°C")
    
    return df

def upload_synthetic_data(df):
    """
    Upload synthetic data to Hopsworks
    """
    api_key = os.getenv('HOPSWORKS_API_KEY')
    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()
    
    # Get or create feature group
    aqi_fg = fs.get_or_create_feature_group(
        name="aqi_features",
        version=1,
        description="AQI and weather features for karachi",
        primary_key=['timestamp'],
        event_time='timestamp',
        online_enabled=False
    )
    
    print("\nUploading to Hopsworks...")
    aqi_fg.insert(df, write_options={"wait_for_job": True})
    
    print(f"✓ Successfully uploaded {len(df)} records to Feature Store!")

if __name__ == "__main__":
    import sys
    
    days = 7 if len(sys.argv) < 2 else int(sys.argv[1])
    
    print(f"\n{'='*60}")
    print(f"SYNTHETIC DATA GENERATOR")
    print(f"{'='*60}\n")
    
    # Create synthetic data
    df = create_synthetic_aqi_data(days=days)
    
    # Save locally
    df.to_csv('data/synthetic_data.csv', index=False)
    print(f"✓ Saved to data/synthetic_data.csv")
    
    # Upload to Hopsworks
    try:
        upload_synthetic_data(df)
        print("\n✓ Data uploaded successfully!")
        print("✓ You can now train the model with: python src/training_pipeline.py")
    except Exception as e:
        print(f"\n✗ Error uploading: {e}")
        print("✓ Data saved locally in data/synthetic_data.csv")