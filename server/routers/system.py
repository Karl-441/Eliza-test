from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from server.core.config import settings
from server.core.llm import llm_engine
from server.core.audio import audio_manager
from server.core.system_control import system_controller
from server.routers.dashboard import get_current_admin
from server.core.i18n import I18N

router = APIRouter()

class MouseMoveRequest(BaseModel):
    x: int
    y: int
    duration: float = 0.5

class MouseClickRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"

class AppLaunchRequest(BaseModel):
    app_name: str

@router.get("/")
def root():
    return {"status": "online", "model": settings.model_path, "version": "1.0.0"}

@router.get("/status")
def get_system_status():
    tts_status = audio_manager.check_tts_health()
    return {
        "llm": {"status": llm_engine.model is not None, "message": I18N.t("model_loaded") if llm_engine.model else I18N.t("model_missing")},
        "tts": tts_status,
        "asr": {"status": True, "message": I18N.t("asr_ready")} 
    }

@router.post("/control/mouse/move")
def move_mouse(data: MouseMoveRequest, user: dict = Depends(get_current_admin)):
    success = system_controller.move_mouse(data.x, data.y, data.duration)
    if not success:
        raise HTTPException(status_code=500, detail=I18N.t("mouse_move_fail"))
    return {"status": "success"}

@router.post("/control/mouse/click")
def click_mouse(data: MouseClickRequest, user: dict = Depends(get_current_admin)):
    success = system_controller.click_mouse(data.x, data.y, data.button)
    if not success:
        raise HTTPException(status_code=500, detail=I18N.t("mouse_click_fail"))
    return {"status": "success"}

@router.post("/control/launch")
def launch_app(data: AppLaunchRequest, user: dict = Depends(get_current_admin)):
    success = system_controller.launch_app(data.app_name)
    if not success:
        raise HTTPException(status_code=403, detail=I18N.t("app_launch_fail"))
    return {"status": "success"}

@router.get("/control/processes")
def list_processes(user: dict = Depends(get_current_admin)):
    return system_controller.get_running_processes()
