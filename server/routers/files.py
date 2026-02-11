from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from server.core.file_analysis import file_analyzer
from server.routers.dashboard import get_current_user
from server.core.i18n import I18N
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=I18N.t("error_file_analysis_failed", error=str(e)))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/files/output")
def list_output_files(user: dict = Depends(get_current_user)):
    """List files in the server output directory"""
    output_dir = os.path.join(os.getcwd(), "server", "output")
    if not os.path.exists(output_dir):
        return {"files": []}
    
    files = []
    for f in os.listdir(output_dir):
        full_path = os.path.join(output_dir, f)
        if os.path.isfile(full_path):
            # Return relative path for download
            files.append({
                "name": f,
                "url": f"/output/{f}",
                "size": os.path.getsize(full_path),
                "mtime": os.path.getmtime(full_path)
            })
    return {"files": files}
