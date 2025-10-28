"""
Upload backup CSV data to Hopsworks
"""
import pandas as pd
import hopsworks
import os
from dotenv import load_dotenv

load_dotenv()

# Find the most recent backup file
backup_files = [f for f in os.listdir('data') if f.startswith('backfill_progress_')]
if not backup_files:
    print("❌ No backup files found!")
    print("Please run: python src/feature_pipeline.py --backfill 7")
    exit(1)

# Load the most recent backup
latest_backup = sorted(backup_files)[-1]
print(f"Loading backup file: data/{latest_backup}")
df = pd.read_csv(f'data/{latest_backup}')

print(f"✓ Loaded {len(df)} records")
print(f"Columns: {df.columns.tolist()}")

# Connect to Hopsworks
api_key = os.getenv('HOPSWORKS_API_KEY')
project = hopsworks.login(api_key_value=api_key)
fs = project.get_feature_store()

# Convert timestamp to datetime if it's string
if df['timestamp'].dtype == 'object':
    df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create feature group with ALL columns
aqi_fg = fs.get_or_create_feature_group(
    name="aqi_features",
    version=1,
    description="AQI and weather features for karachi",
    primary_key=['timestamp'],
    event_time='timestamp',
    online_enabled=False
)

# Upload data
print("Uploading to Hopsworks...")
aqi_fg.insert(df, write_options={"wait_for_job": True})

print(f"\n✓ Successfully uploaded {len(df)} records to Feature Store!")
print("✓ You can now train the model!")