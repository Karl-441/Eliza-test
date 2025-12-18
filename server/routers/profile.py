from fastapi import APIRouter, HTTPException, Body
from server.core.memory import memory_manager

router = APIRouter()

@router.get("/")
async def get_profile():
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
    return {"status": "success", "message": "Memory cleared"}
