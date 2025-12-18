import os
import requests
import sys
from tqdm import tqdm

# Configuration
MODELS_DIR = "models"
LLM_DIR = os.path.join(MODELS_DIR, "llm")
ASR_DIR = os.path.join(MODELS_DIR, "asr")
TTS_DIR = os.path.join(MODELS_DIR, "tts")

# Recommended Model: Qwen2.5-1.5B-Instruct-GGUF (Q4_K_M) - ~1.0 GB, very fast, good instruction following
LLM_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
LLM_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"

def download_file(url, dest_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    if os.path.exists(dest_path):
        if os.path.getsize(dest_path) == total_size:
            print(f"File already exists and is complete: {dest_path}")
            return True
        else:
            print(f"Incomplete file found, restarting download: {dest_path}")
    
    print(f"Downloading {url}...")
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    
    with open(dest_path, 'wb') as f:
        for data in response.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()
    
    if total_size != 0 and t.n != total_size:
        print("ERROR, something went wrong")
        return False
    return True

def main():
    print("=== ELIZA Model Downloader ===")
    
    # Create directories
    for d in [LLM_DIR, ASR_DIR, TTS_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory: {d}")

    # Download LLM
    llm_path = os.path.join(LLM_DIR, LLM_FILENAME)
    print(f"\n[1/2] Checking LLM Model...")
    try:
        download_file(LLM_URL, llm_path)
        print(f"LLM Ready: {llm_path}")
        
        # Update config/settings.json or let the user know
        print(f"\nIMPORTANT: Please ensure your 'server/core/config.py' or 'settings.json' points to:")
        print(f"model_path = '{llm_path}'")
        
    except Exception as e:
        print(f"Failed to download LLM: {e}")

    # TTS Info
    print(f"\n[2/2] Checking TTS Model...")
    print("For GPT-SoVITS, please download your character models (SoVITS .pth and GPT .ckpt) and place them in 'models/tts/'.")
    print("Refer to GPT-SoVITS documentation for model training/downloading.")

    print("\n=== Download Complete ===")

if __name__ == "__main__":
    main()
