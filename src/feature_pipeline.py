"""
Feature Pipeline: Fetch, process, and store AQI data from OpenWeather API
This script runs hourly to collect fresh data
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import hopsworks
from utils import (
    get_env_variable, 
    create_time_features,
    calculate_lagged_features,
    calculate_rolling_features,
    calculate_change_features,
    handle_missing_values,
    print_data_summary
)

class AQIFeaturePipeline:
    """
    Pipeline for collecting and processing AQI data from OpenWeather
    """
    
    def __init__(self):
        """Initialize pipeline with API credentials"""
        self.openweather_api_key = get_env_variable('OPENWEATHER_API_KEY')
        self.hopsworks_api_key = get_env_variable('HOPSWORKS_API_KEY')
        self.city_name = get_env_variable('CITY_NAME', default='karachi')
        self.city_lat = float(get_env_variable('CITY_LATITUDE', default='24.8607'))
        self.city_lon = float(get_env_variable('CITY_LONGITUDE', default='67.0011'))
        self.project = None
        self.fs = None
        
    def fetch_current_aqi_data(self):
        """
        Fetch current air quality and weather data from OpenWeather API
        
        Returns:
            dict: Combined weather and air pollution data
        """
        print(f"Fetching data for {self.city_name}...")
        
        try:
            # Fetch Air Pollution Data
            air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={self.city_lat}&lon={self.city_lon}&appid={self.openweather_api_key}"
            air_response = requests.get(air_url, timeout=10)
            air_response.raise_for_status()
            air_data = air_response.json()
            
            # Fetch Weather Data
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={self.city_lat}&lon={self.city_lon}&appid={self.openweather_api_key}&units=metric"
            weather_response = requests.get(weather_url, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            print(f"✓ Successfully fetched data from OpenWeather")
            
            return {
                'air_pollution': air_data,
                'weather': weather_data
            }
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching data: {e}")
            return None
    
    def extract_features(self, raw_data):
        """
        Extract and engineer features from OpenWeather API data
        
        Args:
            raw_data (dict): Raw data from OpenWeather API
            
        Returns:
            dict: Processed features
        """
        if raw_data is None:
            return None
        
        timestamp = datetime.now()
        
        # Extract air pollution data
        air_list = raw_data.get('air_pollution', {}).get('list', [])
        if not air_list:
            print("✗ No air pollution data available")
            return None
            
        air_components = air_list[0].get('components', {})
        aqi = air_list[0].get('main', {}).get('aqi', None)
        
        # Convert OpenWeather AQI (1-5 scale) to US EPA AQI (0-500 scale)
        # OpenWeather: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
        # Approximate conversion to US EPA scale
        aqi_conversion = {1: 25, 2: 75, 3: 125, 4: 175, 5: 250}
        converted_aqi = aqi_conversion.get(aqi, 100)
        
        # Extract weather data
        weather = raw_data.get('weather', {})
        main = weather.get('main', {})
        wind = weather.get('wind', {})
        
        features = {
            'timestamp': timestamp,
            'city': self.city_name,
            
            # AQI (converted to US EPA scale approximation)
            'aqi': converted_aqi,
            'aqi_openweather': aqi,  # Keep original 1-5 scale too
            
            # Pollutant concentrations (μg/m³)
            'pm25': air_components.get('pm2_5', None),
            'pm10': air_components.get('pm10', None),
            'o3': air_components.get('o3', None),
            'no2': air_components.get('no2', None),
            'so2': air_components.get('so2', None),
            'co': air_components.get('co', None) / 1000 if air_components.get('co') else None,  # Convert to mg/m³
            'no': air_components.get('no', None),
            'nh3': air_components.get('nh3', None),
            
            # Weather conditions
            'temperature': main.get('temp', None),
            'feels_like': main.get('feels_like', None),
            'humidity': main.get('humidity', None),
            'pressure': main.get('pressure', None),
            'wind_speed': wind.get('speed', None),
            'wind_deg': wind.get('deg', None),
            'clouds': weather.get('clouds', {}).get('all', None),
            
            # Location
            'latitude': self.city_lat,
            'longitude': self.city_lon,
        }
        
        # Add time-based features
        time_features = create_time_features(timestamp)
        features.update(time_features)
        
        return features
    
    def engineer_advanced_features(self, df):
        """
        Create advanced engineered features from historical data
        
        Args:
            df (pd.DataFrame): Dataframe with basic features
            
        Returns:
            pd.DataFrame: Dataframe with advanced features
        """
        print("Engineering advanced features...")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Create lagged features (past values)
        df = calculate_lagged_features(df, column='aqi', lags=[1, 3, 6, 12, 24])
        
        # Create rolling window features (moving averages)
        df = calculate_rolling_features(df, column='aqi', windows=[3, 6, 12, 24])
        
        # Create change features (rate of change)
        df = calculate_change_features(df, column='aqi')
        
        # Pollutant ratios (can be predictive)
        if 'pm25' in df.columns and 'pm10' in df.columns:
            df['pm25_pm10_ratio'] = df['pm25'] / (df['pm10'] + 1e-6)
        
        # Temperature-humidity interaction
        if 'temperature' in df.columns and 'humidity' in df.columns:
            df['temp_humidity_interaction'] = df['temperature'] * df['humidity']
        
        print(f"✓ Created {df.shape[1]} total features")
        return df
    
    def connect_to_feature_store(self):
        """
        Connect to Hopsworks Feature Store
        """
        try:
            print("Connecting to Hopsworks...")
            self.project = hopsworks.login(api_key_value=self.hopsworks_api_key)
            self.fs = self.project.get_feature_store()
            print("✓ Connected to Feature Store")
        except Exception as e:
            print(f"✗ Error connecting to Hopsworks: {e}")
            raise
    
    def upload_to_feature_store(self, df):
        """
        Upload processed features to Hopsworks Feature Store
        
        Args:
            df (pd.DataFrame): Dataframe with features
        """
        if self.fs is None:
            self.connect_to_feature_store()
        
        try:
            print("Uploading to Feature Store...")
            
            # Get or create feature group
            aqi_fg = self.fs.get_or_create_feature_group(
                name="aqi_features",
                version=1,
                description=f"AQI and weather features for {self.city_name}",
                primary_key=['timestamp'],
                event_time='timestamp',
                online_enabled=False
            )
            
            # Insert data
            aqi_fg.insert(df, write_options={"wait_for_job": False})
            
            print(f"✓ Successfully uploaded {len(df)} rows to Feature Store")
            
        except Exception as e:
            print(f"✗ Error uploading to Feature Store: {e}")
            # Save locally as backup
            import os
            os.makedirs('data', exist_ok=True)
            df.to_csv(f'data/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', index=False)
            print("✓ Saved backup locally")
    
    def run_pipeline(self):
        """
        Execute the complete feature pipeline
        """
        print("\n" + "="*60)
        print(f"FEATURE PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Step 1: Fetch current data
        raw_data = self.fetch_current_aqi_data()
        
        if raw_data is None:
            print("✗ Pipeline failed: No data fetched")
            return False
        
        # Step 2: Extract features
        features = self.extract_features(raw_data)
        
        if features is None:
            print("✗ Pipeline failed: Feature extraction failed")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        print(f"\nExtracted features:")
        print(f"  - AQI: {features.get('aqi', 'N/A')}")
        print(f"  - PM2.5: {features.get('pm25', 'N/A')}")
        print(f"  - Temperature: {features.get('temperature', 'N/A')}°C")
        print(f"  - Humidity: {features.get('humidity', 'N/A')}%")
        
        # Step 3: Fetch historical data and engineer features
        try:
            self.connect_to_feature_store()
            aqi_fg = self.fs.get_feature_group("aqi_features", version=1)
            historical_df = aqi_fg.read()
            
            # Combine with new data
            combined_df = pd.concat([historical_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
            
            # Engineer features on combined data
            combined_df = self.engineer_advanced_features(combined_df)
            
            # Keep only the new row with all features
            df_to_upload = combined_df.tail(1)
            
        except Exception as e:
            print(f"Note: Could not fetch historical data ({e}). Uploading basic features only.")
            df_to_upload = df
        
        # Step 4: Upload to Feature Store
        self.upload_to_feature_store(df_to_upload)
        
        print("\n✓ Pipeline completed successfully!")
        print("="*60 + "\n")
        
        return True

def backfill_historical_data(days=7, sleep_seconds=10):
    """
    Backfill historical data by running pipeline multiple times
    WARNING: Only use this for initial setup. Don't run repeatedly!
    
    Args:
        days (int): Number of days to backfill
        sleep_seconds (int): Seconds to wait between requests
    """
    pipeline = AQIFeaturePipeline()
    
    print(f"\n{'='*60}")
    print(f"BACKFILLING {days} DAYS OF DATA")
    print(f"This will take approximately {(days * 24 * sleep_seconds) / 3600:.1f} hours")
    print(f"{'='*60}\n")
    
    all_features = []
    
    for i in range(days * 24):  # Hourly for N days
        print(f"\nCollection {i+1}/{days*24}")
        
        raw_data = pipeline.fetch_current_aqi_data()
        
        if raw_data:
            features = pipeline.extract_features(raw_data)
            if features:
                all_features.append(features)
        
        if (i + 1) % 24 == 0:  # Every 24 hours, save progress
            df = pd.DataFrame(all_features)
            import os
            os.makedirs('data', exist_ok=True)
            df.to_csv(f'data/backfill_progress_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
            print(f"✓ Progress saved: {len(all_features)} records")
        
        time.sleep(sleep_seconds)
    
    # Final processing and upload
    if all_features:
        df = pd.DataFrame(all_features)
        df = pipeline.engineer_advanced_features(df)
        pipeline.upload_to_feature_store(df)
        print(f"\n✓ Backfill complete! Uploaded {len(df)} records")

if __name__ == "__main__":
    import sys
    
    # Check if backfill mode
    if len(sys.argv) > 1 and sys.argv[1] == '--backfill':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        backfill_historical_data(days=days)
    else:
        # Normal mode: run once
        pipeline = AQIFeaturePipeline()
        pipeline.run_pipeline()