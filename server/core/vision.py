import os
import logging
from typing import List, Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)

class VisionManager:
    def __init__(self):
        self.model = None
        self.enabled = settings.enable_vision
        self.model_path = settings.vision_model_path
        
        if self.enabled:
            self.load_model()

    def load_model(self):
        if not os.path.exists(self.model_path):
            logger.warning(f"YOLO model not found at {self.model_path}. Vision features disabled.")
            return

        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model from {self.model_path}...")
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully.")
        except ImportError:
            logger.error("ultralytics package not installed. Cannot load Vision model.")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")

    def detect(self, image_source: Any) -> List[Dict[str, Any]]:
        """
        Run detection on an image.
        image_source can be a file path, URL, PIL Image, or numpy array.
        """
        if not self.model:
            if self.enabled:
                self.load_model()
            if not self.model:
                return []

        try:
            results = self.model(image_source)
            detections = []
            
            for r in results:
                # Iterate over boxes
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = self.model.names[cls_id]
                    coords = box.xyxy[0].tolist() # [x1, y1, x2, y2]
                    
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "box": coords
                    })
            
            return detections
        except Exception as e:
            logger.error(f"Vision detection error: {e}")
            return []

    def analyze_scene(self, image_source: Any) -> str:
        """
        Returns a descriptive string of the scene based on detections.
        """
        detections = self.detect(image_source)
        if not detections:
            return "I don't see anything recognizable."
        
        # Count objects
        counts = {}
        for d in detections:
            l = d['label']
            counts[l] = counts.get(l, 0) + 1
            
        desc_parts = []
        for label, count in counts.items():
            if count == 1:
                desc_parts.append(f"a {label}")
            else:
                desc_parts.append(f"{count} {label}s")
        
        return "I see " + ", ".join(desc_parts) + "."

vision_manager = VisionManager()
