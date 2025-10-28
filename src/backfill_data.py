from datetime import datetime, timedelta
import time

def backfill_historical_data(days=30):
    """
    Collect historical data by running feature pipeline repeatedly
    """
    all_features = []
    
    for i in range(days * 24):  # hourly for 'days' days
        # Fetch and process current data
        raw_data = fetch_aqi_data()
        features = extract_features(raw_data)
        
        if features:
            all_features.append(features)
        
        # Wait 1 hour (3600 seconds)
        # For testing, use time.sleep(10) instead
        time.sleep(3600)
    
    # Convert to DataFrame
    df = pd.DataFrame(all_features)
    df = engineer_features(df)
    
    # Upload to Feature Store
    upload_to_feature_store(df)