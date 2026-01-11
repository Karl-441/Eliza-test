from fastapi import APIRouter, Depends
from server.core.projects import projects_store
from server.routers.dashboard import get_current_user

router = APIRouter()

@router.post("/")
def create_project(payload: dict, user: dict = Depends(get_current_user)):
    name = payload.get("name", "")
    owner_user = user.get("user", "")
    # Only from authenticated users; bind to their client_secret if exists
    from server.core.users import user_manager
    u = user_manager.users.get(owner_user)
    owner_key = u.client_secret if u else ""
    return projects_store.create_project(name, owner_key, owner_user)

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
