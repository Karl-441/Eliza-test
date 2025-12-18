import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = str(BASE_DIR / "data" / "server_state.json")

@dataclass
class ServerState:
    last_model: Optional[str] = None
    last_loaded_at: Optional[str] = None

class StateManager:
    def __init__(self):
        self.state = ServerState()
        self.load()

    def load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Filter only valid keys
                    valid_keys = ServerState.__annotations__.keys()
                    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                    self.state = ServerState(**filtered_data)
            except Exception as e:
                print(f"Failed to load server state: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self.state), f, indent=4)
        except Exception as e:
            print(f"Failed to save server state: {e}")

    def set_last_model(self, model_name: str):
        self.state.last_model = model_name
        self.state.last_loaded_at = datetime.datetime.now().isoformat()
        self.save()

    def get_last_model(self) -> Optional[str]:
        return self.state.last_model

state_manager = StateManager()
