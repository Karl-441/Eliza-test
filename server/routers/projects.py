from fastapi import APIRouter, Depends, Body
from server.core.projects import projects_store
from server.routers.dashboard import get_current_user
from server.core.orchestrator import orchestrate
from server.core.framework.bus import message_bus
from server.core.framework.events import Event
from server.core.i18n import I18N
import uuid

router = APIRouter()

@router.post("/")
def create_project(payload: dict, user: dict = Depends(get_current_user)):
    name = payload.get("name", "")
    template = payload.get("template", "") # Support template from payload
    owner_user = user.get("user", "")
    # Only from authenticated users; bind to their client_secret if exists
    from server.core.users import user_manager
    u = user_manager.users.get(owner_user)
    owner_key = u.client_secret if u else ""
    # Pass template to projects_store
    return projects_store.create_project(name, owner_key, owner_user, template=template)

@router.get("/")
def list_projects(user: dict = Depends(get_current_user)):
    role = user.get("role", "guest")
    if role == "admin":
        return projects_store.list_all()
    if role == "user":
        return projects_store.list_by_owner_user(user.get("user",""))
    return {"projects": []}

@router.post("/{project_id}/agents")
def create_agent(project_id: str, payload: dict, user: dict = Depends(get_current_user)):
    role_name = payload.get("role_name", "")
    model_name = payload.get("model_name", "")
    description = payload.get("description", "")
    return projects_store.add_agent(project_id, role_name, model_name, description)

@router.get("/{project_id}/agents")
def list_agents(project_id: str, user: dict = Depends(get_current_user)):
    return projects_store.list_agents(project_id)

@router.get("/{project_id}/log")
def get_log(project_id: str, user: dict = Depends(get_current_user)):
    return projects_store.get_log(project_id)

@router.post("/{project_id}/orchestrate")
async def trigger_orchestration(project_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    message = payload.get("message", "")
    user_id = user.get("user", "unknown")
    if not message:
        return {"error": I18N.t("proj_msg_required")}
    
    # Run orchestration
    result = await orchestrate(project_id, message, user_id)
    return result

from server.core.database import SessionLocal
from server.core.models import WorkflowState
import json

@router.get("/{project_id}/workflow")
def get_workflow_state(project_id: str, user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        # Get latest state
        state = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).order_by(WorkflowState.updated_at.desc()).first()
        if not state:
            return {"status": "idle", "tasks": []}
        
        return {
            "id": state.id,
            "status": state.status,
            "tasks": json.loads(state.tasks) if state.tasks else [],
            "updated_at": state.updated_at
        }
    finally:
        db.close()

@router.post("/{project_id}/control")
async def control_workflow(project_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    action = payload.get("action") # pause, resume, approve, reject
    message = payload.get("message", "") # For reject reason or approve comment
    
    if action not in ["pause", "resume", "approve", "reject"]:
        return {"error": I18N.t("proj_invalid_action")}
    
    await message_bus.publish(Event(
        topic="orchestrator",
        type="orchestration.control",
        data={"action": action, "project_id": project_id, "message": message},
        correlation_id=str(uuid.uuid4())
    ))
    
    return {"status": "command_sent", "action": action}

@router.post("/{project_id}/init_team")
def initialize_team(project_id: str, user: dict = Depends(get_current_user)):
    return projects_store.init_dev_team(project_id)
