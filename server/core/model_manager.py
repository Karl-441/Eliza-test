import os
import glob
import logging
from typing import List, Dict
from .config import settings
from .llm import llm_engine

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, models_dir="models/llm"):
        self.models_dir = models_dir

    def list_models(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.models_dir):
            return []
        
        # Look for .gguf files
        files = glob.glob(os.path.join(self.models_dir, "*.gguf"))
        models = []
        for f in files:
            models.append({
                "name": os.path.basename(f),
                "path": f,
                "size_mb": round(os.path.getsize(f) / (1024*1024), 2)
            })
        return models

    def load_model(self, model_name: str) -> bool:
        # Security check: ensure path is within models_dir
        target_path = os.path.join(self.models_dir, model_name)
        target_path = os.path.abspath(target_path)
        
        # Basic path traversal check
        if not target_path.startswith(os.path.abspath(self.models_dir)):
            logger.error(f"Invalid model path: {target_path}")
            return False

        if not os.path.exists(target_path):
            logger.error(f"Model not found: {target_path}")
            return False

        # Update settings
        settings.model_path = target_path
        settings.save()
        
        # Trigger reload
        try:
            llm_engine.reload_model()
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

model_manager = ModelManager()
