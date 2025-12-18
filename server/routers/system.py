from fastapi import APIRouter
from server.core.config import settings
from server.core.llm import llm_engine
from server.core.audio import audio_manager

router = APIRouter()

@router.get("/")
def root():
    return {"status": "online", "model": settings.model_path, "version": "1.0.0"}

@router.get("/status")
def get_system_status():
    tts_status = audio_manager.check_tts_health()
    return {
        "llm": {"status": llm_engine.model is not None, "message": "Model Loaded" if llm_engine.model else "Model Missing"},
        "tts": tts_status,
        "asr": {"status": True, "message": "Ready (On Demand)"} 
    }
