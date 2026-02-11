from fastapi import APIRouter, HTTPException, Body, Depends
from server.core.memory import memory_manager
from server.routers.dashboard import get_current_user
from server.core.i18n import I18N

router = APIRouter()

from server.core.persona import persona_manager

@router.get("/persona")
async def get_persona(user: dict = Depends(get_current_user)):
    return persona_manager.get_persona()

@router.post("/persona/analyze")
async def analyze_persona(user: dict = Depends(get_current_user)):
    persona_manager.analyze_memory()
    return {"status": "success", "persona": persona_manager.get_persona()}

@router.get("/")
async def get_user_profile(user: dict = Depends(get_current_user)):
    return memory_manager.user_profile

@router.post("/")
async def update_profile(profile: dict = Body(...)):
    for k, v in profile.items():
        memory_manager.update_profile(k, v)
    return memory_manager.user_profile

@router.get("/export")
async def export_profile():
    return {"json": memory_manager.export_profile_json()}

@router.post("/import")
async def import_profile(profile: dict = Body(..., embed=True)):
    memory_manager.import_profile(profile)
    return {"status": "success", "profile": memory_manager.user_profile}

@router.delete("/memory")
async def clear_memory():
    memory_manager.clear_history()
    return {"status": "success", "message": I18N.t("memory_cleared")}
