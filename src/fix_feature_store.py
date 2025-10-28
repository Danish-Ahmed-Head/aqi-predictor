"""
Fix Feature Store - Delete and recreate feature group
"""
import hopsworks
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Hopsworks
api_key = os.getenv('HOPSWORKS_API_KEY')
project = hopsworks.login(api_key_value=api_key)
fs = project.get_feature_store()

try:
    # Get the old feature group
    aqi_fg = fs.get_feature_group("aqi_features", version=1)
    
    # Delete it
    aqi_fg.delete()
    print("✓ Old feature group deleted successfully!")
    
except Exception as e:
    print(f"Feature group doesn't exist or already deleted: {e}")

print("\n✓ Feature Store is now clean. Ready for fresh data upload!")