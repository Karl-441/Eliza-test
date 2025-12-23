import os
import json
import hashlib
import sys
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "model_config.json"
MODELS_DIR = BASE_DIR / "Models" / "llm"
BAT_OUTPUT_PATH = BASE_DIR.parent / "download_models.bat"

def calculate_hash(file_path, algorithm='sha256'):
    # In a real scenario, this would check the hash. 
    # For now, we'll skip hash check implementation in the BAT generation for simplicity unless required.
    pass

def scan_models():
    print(f"Scanning models configuration from: {CONFIG_PATH}")
    
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    missing_models = []
    
    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Checking models in: {MODELS_DIR}")
    
    for model in config.get("models", []):
        model_path = MODELS_DIR / model["name"]
        if not model_path.exists():
            print(f"[-] Missing: {model['name']}")
            missing_models.append(model)
        else:
            print(f"[+] Found: {model['name']}")

    if missing_models:
        print(f"\nFound {len(missing_models)} missing models. Generating download script...")
        generate_bat_script(missing_models)
    else:
        print("\nAll models are present.")
        if BAT_OUTPUT_PATH.exists():
             os.remove(BAT_OUTPUT_PATH) # Cleanup if everything is fine

def generate_bat_script(models):
    # BAT script content
    # We will use 'curl' which is available on modern Windows
    
    content = ["@echo off", "setlocal", "title Eliza Model Downloader", ""]
    
    # Set directory
    content.append(f"set \"TARGET_DIR={MODELS_DIR}\"")
    content.append("if not exist \"%TARGET_DIR%\" mkdir \"%TARGET_DIR%\"")
    content.append("cd /d \"%TARGET_DIR%\"")
    content.append("")
    
    for model in models:
        name = model["name"]
        url = model["url"]
        content.append(f"echo Downloading {name}...")
        content.append(f"echo URL: {url}")
        # -L for follow redirects, -O for output to file, --fail to fail on error
        content.append(f"curl -L -o \"{name}\" \"{url}\" --fail")
        content.append("if %errorlevel% neq 0 (")
        content.append(f"    echo Error downloading {name}. Retrying...")
        content.append(f"    curl -L -o \"{name}\" \"{url}\" --retry 3")
        content.append(")")
        content.append(f"if exist \"{name}\" echo [OK] {name} downloaded.")
        content.append("")
        
    content.append("echo.")
    content.append("echo All downloads processed.")
    content.append("pause")
    
    with open(BAT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
        
    print(f"Script generated at: {BAT_OUTPUT_PATH}")
    print("Please run 'download_models.bat' to download missing files.")

if __name__ == "__main__":
    scan_models()
