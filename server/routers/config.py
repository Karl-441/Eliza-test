from fastapi import APIRouter, HTTPException, Body
from server.core.config import settings
from server.core.prompts import prompt_manager, PromptTemplate
from server.core.i18n import I18N

router = APIRouter()

@router.get("/")
async def get_config():
    # Return safe subset of settings
    return {
        "model_path": settings.model_path,
        "n_ctx": settings.n_ctx,
        "n_threads": settings.n_threads,
        "temperature": settings.temperature,
        "enable_audio": settings.enable_audio,
        "enable_search": settings.enable_search
    }

@router.post("/")
async def update_config(config: dict = Body(...)):
    # Validate and update settings
    # This needs proper implementation in Settings class to update runtime/file
    # For now, simplistic update
    for k, v in config.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    settings.save()
    return {"status": "success", "message": I18N.t("config_updated")}

@router.get("/prompts/active")
async def get_active_prompt():
    return {"id": prompt_manager.config.active_id}

@router.post("/prompts/active")
async def set_active_prompt(template_id: str = Body(..., embed=True)):
    if prompt_manager.set_active(template_id):
        return {"status": "success", "active_id": template_id}
    raise HTTPException(status_code=404, detail=I18N.t("template_not_found"))

@router.get("/prompts")
async def list_prompts():
    return prompt_manager.list_templates()

@router.post("/prompts")
async def save_prompt(prompt: dict = Body(...)):
    try:
        template = PromptTemplate(**prompt)
        prompt_manager.add_template(template)
        return {"status": "success", "id": template.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    if prompt_manager.delete_template(prompt_id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail=I18N.t("template_not_found"))

