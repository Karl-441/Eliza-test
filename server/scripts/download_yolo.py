import os
import requests
import sys
from pathlib import Path
from tqdm import tqdm

# Configuration
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
MODEL_FILENAME = "yolov8n.pt"
DEST_DIR = Path(__file__).resolve().parent.parent / "Models" / "vision"

def download_file(url, dest_path):
    retries = 3
    for attempt in range(retries):
        try:
            print(f"Downloading {url} to {dest_path} (Attempt {attempt+1}/{retries})")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 # 1 Kibibyte
            
            with open(dest_path, 'wb') as file, tqdm(
                desc=dest_path.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(block_size):
                    size = file.write(data)
                    bar.update(size)
                    
            print("\nDownload complete!")
            return True
        except Exception as e:
            print(f"\nError downloading file: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            import time
            time.sleep(2)
    return False

def main():
    # Ensure directory exists
    if not DEST_DIR.exists():
        print(f"Creating directory: {DEST_DIR}")
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        
    dest_path = DEST_DIR / MODEL_FILENAME
    
    if dest_path.exists():
        print(f"Model already exists at {dest_path}")
        # Optional: Check size or hash to verify integrity
        if dest_path.stat().st_size > 0:
            print("Skipping download.")
            return
        else:
            print("File is empty, re-downloading...")
    
    success = download_file(MODEL_URL, dest_path)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
