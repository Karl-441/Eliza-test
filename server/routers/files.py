from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from server.core.file_analysis import file_analyzer
from server.routers.dashboard import get_current_user
import shutil
import os
import tempfile

router = APIRouter(tags=["File Analysis"])

@router.post("/files/analyze")
async def analyze_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    # Limit file size? FastAPI handles upload limits but good to be aware
    
    # Save to temp
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        result = file_analyzer.analyze_file(tmp_path)
        # Inject original filename since temp file has random name
        result["filename"] = file.filename
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
