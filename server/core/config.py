import os
import json
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LLM_DIR = BASE_DIR / "Models" / "llm"

class Settings(BaseModel):
    # LLM Settings
    models_root_dir: str = str(BASE_DIR / "Models" / "llm")
    model_path: str = str(LLM_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf")
    default_model_name: str = "server-qwen2.5-7b"  # Logical name used in projects
    n_ctx: int = 4096
    n_threads: int = 4
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    language: str = "zh"
    
    # Search Settings
    enable_search: bool = True

    # Audio Settings
    enable_audio: bool = False
    tts_api_url: str = "http://127.0.0.1:9880"  # Default GPT-SoVITS port
    tts_speed: float = 1.0
    tts_volume: float = 1.0
    tts_pitch: float = 1.0
    voice_presets: dict = {
        "default": {
            "ref_audio_path": "voices/default.wav",
            "prompt_text": "你好，我是Eliza。",
            "prompt_language": "zh",
            "name": "Default (Eliza)"
        }
    }

    # Vision Settings
    enable_vision: bool = False
    vision_model_path: str = str(BASE_DIR / "Models" / "vision" / "yolov8n.pt")
    
    # Security Settings
    admin_user: str = "admin"
    admin_password_hash: str = "" # Empty means default "admin" (will handle in auth logic) or uninitialized
    jwt_secret: str = "change_this_to_a_random_secret_key"
    client_api_key: str = "eliza-client-key-12345" # Default key for clients
    allowed_apps: list = [
        "notepad.exe", "calc.exe", "explorer.exe", 
        "chrome.exe", "firefox.exe", "msedge.exe"
    ]
    
    # Paths
    memory_path: str = str(DATA_DIR / "memory.json")
    user_profile_path: str = str(DATA_DIR / "user_profile.json")

    # Database Settings
    database_url: str = "sqlite:///./server/data/projects.db"  # Default to SQLite
    vector_dim: int = 384 # Default for all-MiniLM-L6-v2
    
    # OpenAI Settings (for Embeddings/LLM Triggers)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"

    # Local Embedding Settings
    embedding_provider: str = "local" # local or openai
    local_embedding_model: str = "all-MiniLM-L6-v2" # sentence-transformers model

    def save(self, path=None):
        target = Path(path) if path else (CONFIG_DIR / "settings.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.json(indent=4))

    @classmethod
    def load(cls, path=None):
        target = Path(path) if path else (CONFIG_DIR / "settings.json")
        if target.exists():
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                obj = cls(**data)
                
                # Auto-generate secret if default
                if obj.jwt_secret == "change_this_to_a_random_secret_key":
                     import secrets
                     obj.jwt_secret = secrets.token_urlsafe(32)
                     obj.save(path=target)
                return obj
        
        # New instance
        obj = cls()
        import secrets
        obj.jwt_secret = secrets.token_urlsafe(32)
        return obj

settings = Settings.load()
