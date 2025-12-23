from fastapi import APIRouter, UploadFile, File, HTTPException
from server.core.vision import vision_manager
import shutil
import os
import tempfile

router = APIRouter(prefix="/api/v1/vision", tags=["vision"])

@router.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    if not vision_manager.enabled:
        raise HTTPException(status_code=503, detail="Vision features are disabled")
    
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        detections = vision_manager.detect(tmp_path)
        return {"detections": detections}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/analyze")
async def analyze_scene(file: UploadFile = File(...)):
    if not vision_manager.enabled:
        raise HTTPException(status_code=503, detail="Vision features are disabled")
    
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        description = vision_manager.analyze_scene(tmp_path)
        return {"description": description}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
