"""
Collect Real Data Over Time
This script should run continuously or via scheduler to collect actual time-series data
"""
import time
from datetime import datetime
from feature_pipeline import AQIFeaturePipeline

def collect_continuous_data(hours=24, interval_minutes=60):
    """
    Collect data at specified intervals
    
    Args:
        hours (int): How many hours to collect data
        interval_minutes (int): Minutes between each collection
    """
    pipeline = AQIFeaturePipeline()
    
    total_collections = int(hours * (60 / interval_minutes))
    interval_seconds = interval_minutes * 60
    
    print(f"\n{'='*60}")
    print(f"CONTINUOUS DATA COLLECTION")
    print(f"{'='*60}")
    print(f"Duration: {hours} hours")
    print(f"Interval: {interval_minutes} minutes")
    print(f"Total collections: {total_collections}")
    print(f"{'='*60}\n")
    
    for i in range(total_collections):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collection {i+1}/{total_collections}")
        
        try:
            success = pipeline.run_pipeline()
            if success:
                print(f"✓ Collection successful")
            else:
                print(f"✗ Collection failed")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        if i < total_collections - 1:  # Don't sleep after last collection
            print(f"⏳ Waiting {interval_minutes} minutes until next collection...")
            time.sleep(interval_seconds)
    
    print(f"\n{'='*60}")
    print(f"✓ DATA COLLECTION COMPLETE!")
    print(f"Collected {total_collections} samples over {hours} hours")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    
    # Default: collect for 24 hours at 1-hour intervals
    hours = 24
    interval = 60  # minutes
    
    if len(sys.argv) > 1:
        hours = int(sys.argv[1])
    if len(sys.argv) > 2:
        interval = int(sys.argv[2])
    
    print(f"\nStarting data collection:")
    print(f"  Duration: {hours} hours")
    print(f"  Interval: {interval} minutes")
    print(f"\nPress Ctrl+C to stop at any time.\n")
    
    try:
        collect_continuous_data(hours=hours, interval_minutes=interval)
    except KeyboardInterrupt:
        print("\n\n✗ Collection stopped by user")
        print("Data collected so far has been saved to Feature Store")