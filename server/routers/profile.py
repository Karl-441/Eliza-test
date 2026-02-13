from fastapi import APIRouter, HTTPException, Body, Depends
from server.core.memory import memory_manager, vector_store
from server.routers.dashboard import get_current_user
from server.core.i18n import I18N

router = APIRouter()

from server.core.persona import persona_manager

@router.get("/layers/{layer_name}")
def get_layer_memories(layer_name: str, user: dict = Depends(get_current_user)):
    if layer_name not in ["instinct", "subconscious", "active_recall"]:
        raise HTTPException(status_code=400, detail="Invalid layer name")
    
    memories = vector_store.get_all_memories(layer_name)
    return {"layer": layer_name, "count": len(memories), "memories": memories}

@router.post("/layers/{layer_name}/search")
def search_layer(layer_name: str, query: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    if layer_name == "instinct":
        return vector_store.search_instinct(query)
    elif layer_name == "subconscious":
        return vector_store.search_subconscious(query)
    elif layer_name == "active_recall":
        return vector_store.search_active_recall(query)
    else:
        raise HTTPException(status_code=400, detail="Invalid layer name")

@router.post("/layers/{layer_name}/add")
def add_memory_to_layer(layer_name: str, data: dict = Body(...), user: dict = Depends(get_current_user)):
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    if layer_name == "instinct":
        trait_type = data.get("trait_type", "general")
        return vector_store.add_instinct(content, trait_type)
    elif layer_name == "subconscious":
        keywords = data.get("keywords", "")
        return vector_store.add_subconscious(content, keywords)
    elif layer_name == "active_recall":
        role = data.get("role", "user")
        return vector_store.add_active_recall(content, role)
    else:
        raise HTTPException(status_code=400, detail="Invalid layer name")

@router.delete("/layers/{layer_name}/{memory_id}")
def delete_memory_item(layer_name: str, memory_id: int, user: dict = Depends(get_current_user)):
    success = vector_store.delete_memory(layer_name, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
    return {"status": "success", "message": f"Memory {memory_id} deleted from {layer_name}"}

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
