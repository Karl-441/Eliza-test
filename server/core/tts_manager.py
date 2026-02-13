import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tts_models.json")

class TTSModelConfig(BaseModel):
    id: str
    name: str
    type: str  # female, male, neutral
    language: str # zh, en, ja
    path: Optional[str] = None
    speed: int = 100
    pitch: int = 0
    volume: int = 100
    learning_rate: float = 0.0002
    batch_size: int = 32
    status: str = "active" # active, inactive
    created_at: str
    updated_at: str

class TTSManager:
    def __init__(self):
        self.models: Dict[str, TTSModelConfig] = {}
        self.load_models()

    def load_models(self):
        if not os.path.exists(os.path.dirname(DATA_FILE)):
            os.makedirs(os.path.dirname(DATA_FILE))
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        model = TTSModelConfig(**item)
                        self.models[model.id] = model
            except Exception as e:
                print(f"Error loading TTS models: {e}")
                self.create_default_models()
        else:
            self.create_default_models()

    def create_default_models(self):
        # Create some default models if none exist
        defaults = [
            {
                "name": "Standard Female (ZH)",
                "type": "female",
                "language": "zh",
                "speed": 100, "pitch": 0, "volume": 100
            },
            {
                "name": "Tactical Command (EN)",
                "type": "male",
                "language": "en",
                "speed": 110, "pitch": -2, "volume": 120
            }
        ]
        for d in defaults:
            self.create_model(d)

    def save_models(self):
        data = [m.dict() for m in self.models.values()]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def create_model(self, data: dict) -> TTSModelConfig:
        model_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Merge with defaults for missing fields
        full_data = {
            "id": model_id,
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "learning_rate": 0.0002,
            "batch_size": 32,
            **data
        }
        
        model = TTSModelConfig(**full_data)
        self.models[model_id] = model
        self.save_models()
        return model

    def update_model(self, model_id: str, updates: dict) -> Optional[TTSModelConfig]:
        if model_id not in self.models:
            return None
        
        model = self.models[model_id]
        model_data = model.dict()
        
        # Update fields
        for k, v in updates.items():
            if k in model_data and k != "id" and k != "created_at":
                model_data[k] = v
        
        model_data["updated_at"] = datetime.now().isoformat()
        
        new_model = TTSModelConfig(**model_data)
        self.models[model_id] = new_model
        self.save_models()
        return new_model

    def delete_model(self, model_id: str) -> bool:
        if model_id in self.models:
            del self.models[model_id]
            self.save_models()
            return True
        return False

    def get_model(self, model_id: str) -> Optional[TTSModelConfig]:
        return self.models.get(model_id)

    def list_models(self) -> List[TTSModelConfig]:
        return list(self.models.values())

    def scan_models(self, directory: str) -> List[TTSModelConfig]:
        """Scans a directory for model files and adds them."""
        added_models = []
        if not os.path.exists(directory):
            return []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith((".pth", ".ckpt", ".pt")):
                    # Simple heuristic: use filename as model name
                    name = os.path.splitext(file)[0]
                    # Check if already exists by name (naive check)
                    if any(m.name == name for m in self.models.values()):
                        continue
                    
                    # Guess type/lang from filename
                    m_type = "neutral"
                    if "female" in name.lower(): m_type = "female"
                    elif "male" in name.lower(): m_type = "male"
                    
                    lang = "zh"
                    if "en" in name.lower(): lang = "en"
                    elif "ja" in name.lower(): lang = "ja"

                    new_model = self.create_model({
                        "name": name,
                        "type": m_type,
                        "language": lang,
                        "path": os.path.join(root, file) # We might need to add 'path' to TTSModelConfig if not present
                    })
                    added_models.append(new_model)
        
        return added_models

tts_manager = TTSManager()
