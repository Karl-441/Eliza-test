import asyncio
import json
import logging
import datetime # Added import
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Response, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import secrets
import hashlib
import uuid
import os
from server.core.users import user_manager
from server.core.model_manager import model_manager
from server.core.monitor import monitor, client_manager, audit_logger, monitor_hub
from server.core.llm import llm_engine
from server.core.audio import audio_manager
from server.middleware.auth import verify_api_key
from server.core.i18n import I18N
from server.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Auth Models & Logic ---

class LoginRequest(BaseModel):
    username: str
    password: str

class TTSPreviewRequest(BaseModel):
    text: str
    voice_id: str
    speed: float = 1.0
    volume: float = 1.0
    pitch: float = 1.0 # Added

# Simple session store (in-memory for now)
sessions = {}

def get_current_user(request: Request):
    # 1. Check Cookie Session
    session_id = request.cookies.get("admin_session")
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    # 2. Check API Key Header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Check configured client key
        if api_key == settings.client_api_key:
            return {
                "user": "default_client",
                "role": "user",
                "created_at": str(datetime.datetime.now())
            }

        # Simple search for user by key (inefficient for large DB, but fine here)
        for u in user_manager.users.values():
            if u.client_secret == api_key:
                return {
                    "user": u.username,
                    "role": u.role,
                    "created_at": str(datetime.datetime.now())
                }
    
    raise HTTPException(status_code=401, detail=I18N.t("auth_not_authenticated"))

def get_current_admin(request: Request):
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail=I18N.t("auth_requires_admin"))
    return user

@router.post("/login")
async def login(data: LoginRequest, response: Response):
    user = user_manager.authenticate(data.username, data.password)
    if not user:
        audit_logger.log("LOGIN_FAILED", f"Failed login attempt for {data.username}", "unknown")
        raise HTTPException(status_code=401, detail=I18N.t("auth_invalid_creds"))
        
    session_id = secrets.token_hex(16)
    sessions[session_id] = {
        "user": user.username, 
        "role": user.role,
        "created_at": str(datetime.datetime.now())
    }
    
    response.set_cookie(key="admin_session", value=session_id, httponly=True, max_age=3600)
    audit_logger.log("LOGIN_SUCCESS", f"User {user.username} logged in", "unknown")
    return {"status": "success", "role": user.role}

@router.post("/logout")
async def logout(response: Response, request: Request):
    session_id = request.cookies.get("admin_session")
    if session_id in sessions:
        del sessions[session_id]
    response.delete_cookie("admin_session")
    return {"status": "success"}

@router.get("/check_auth")
async def check_auth(request: Request):
    try:
        user = get_current_user(request)
        return {"authenticated": True, "role": user["role"], "username": user["user"]}
    except HTTPException:
        return {"authenticated": False}

class RegisterRequest(BaseModel):
    username: str
    password: str
    client_name: str

@router.post("/register")
async def register(data: RegisterRequest):
    success, message = user_manager.register_user(data.username, data.password, data.client_name)
    if not success:
        audit_logger.log("REGISTER_FAILED", f"Failed registration for {data.username}: {message}", "unknown")
        raise HTTPException(status_code=400, detail=message)
    audit_logger.log("REGISTER_PENDING", f"User {data.username} registered pending approval", "unknown")
    return {"status": "success", "message": message}

@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    full_user = user_manager.users.get(user["user"])
    if not full_user:
         raise HTTPException(status_code=404, detail="User not found")
    return full_user.notifications

# --- Admin Management ---

@router.get("/admin/users")
async def list_users(user: dict = Depends(get_current_admin)):
    return user_manager.list_users()

@router.post("/admin/users/{username}/approve")
async def approve_user(username: str, user: dict = Depends(get_current_admin)):
    approved_user = user_manager.approve_user(username)
    if not approved_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    audit_logger.log("USER_APPROVE", f"Approved user {username}", user["user"])
    # Mock Notification
    logger.info(f"NOTIFICATION: Sent credentials to {username}. Client ID: {approved_user.client_id}")
    
    return {"status": "success", "user": approved_user.model_dump(exclude={"password_hash"})}

@router.post("/admin/users/{username}/reject")
async def reject_user(username: str, user: dict = Depends(get_current_admin)):
    user_manager.reject_user(username)
    audit_logger.log("USER_REJECT", f"Rejected user {username}", user["user"])
    return {"status": "success"}

# --- Model Management ---

@router.get("/models")
async def list_models(user: dict = Depends(get_current_user)):
    local = model_manager.list_models()
    remote = []
    if user.get("role") == "admin":
        remote = model_manager.get_remote_models()
        # Merge status
        local_names = {m["name"] for m in local}
        for r in remote:
            r["downloaded"] = r["name"] in local_names
    return {"local": local, "remote": remote}

@router.post("/models/download")
async def download_model(request: Request, user: dict = Depends(get_current_admin)):
    data = await request.json()
    url = data.get("url")
    filename = data.get("filename")
    
    if not url or not filename:
        raise HTTPException(status_code=400, detail="URL and filename required")
        
    task_id = model_manager.start_download(url, filename)
    audit_logger.log("MODEL_DOWNLOAD", f"Started download for {filename}", user["user"])
    return {"status": "success", "task_id": task_id}

@router.get("/models/downloads")
async def get_downloads(user: dict = Depends(get_current_user)):
    return model_manager.get_all_downloads()

@router.get("/models/huggingface")
async def search_huggingface(q: str, limit: int = 10, user: dict = Depends(get_current_user)):
    # Proxy to HF API
    import requests
    try:
        # Search for GGUF models specifically as that's what we support
        api_url = f"https://huggingface.co/api/models?search={q}&filter=gguf&limit={limit}&full=true"
        resp = requests.get(api_url, timeout=10)
        if resp.ok:
            return resp.json()
        return []
    except Exception as e:
        logger.error(f"HF Search failed: {e}")
        return []

@router.post("/models/load")
async def load_specific_model(model_name: str, user: dict = Depends(get_current_admin)):
    audit_logger.log("MODEL_LOAD", f"Loading model {model_name}", user["user"])
    if model_manager.load_model(model_name):
        return {"status": "success", "message": f"Model {model_name} loaded"}
    else:
        return {"status": "error", "message": "Failed to load model"}

@router.post("/model/reload")
async def reload_model(user: dict = Depends(get_current_admin)):
    audit_logger.log("MODEL_RELOAD", "Manual model reload triggered", user["user"])
    try:
        llm_engine.reload_model()
        return {"status": "success", "message": "Model reload initiated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from server.core.config import settings
from pydantic import BaseModel

@router.get("/settings")
async def get_settings(user: dict = Depends(get_current_admin)):
    return settings.dict()

@router.post("/settings")
async def update_settings(new_settings: dict, user: dict = Depends(get_current_admin)):
    audit_logger.log("SETTINGS_UPDATE", "Updated system settings", user["user"])
    
    # Update settings object
    for k, v in new_settings.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    
    settings.save()
    return {"status": "success", "settings": settings.dict()}

# --- TTS Preview ---

@router.get("/audio/preview/{filename}")
async def get_audio_preview(filename: str):
    temp_dir = os.path.join(os.path.dirname(settings.memory_path), "temp_audio")
    file_path = os.path.join(temp_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Audio file not found")

@router.post("/tts/preview")
async def tts_preview(data: TTSPreviewRequest, user: dict = Depends(get_current_user)):
    try:
        temp_dir = os.path.join(os.path.dirname(settings.memory_path), "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"preview_{uuid.uuid4()}.wav"
        output_path = os.path.join(temp_dir, filename)
        
        success = audio_manager.text_to_speech(
            text=data.text,
            output_path=output_path,
            speed=data.speed,
            volume=data.volume,
            voice_id=data.voice_id
        )
        
        if success:
            # Construct URL (assuming relative path for now, frontend handles base URL)
            audio_url = f"/api/v1/dashboard/audio/preview/{filename}"
            return {"status": "success", "message": "Preview generated", "audio_url": audio_url}
        else:
             return {"status": "error", "message": "Failed to generate audio"}
             
    except Exception as e:
        logger.error(f"TTS Preview error: {e}")
        return {"status": "error", "message": str(e)} 

class ModelRequest(BaseModel):
    name: str
    link: str | None = None
    reason: str

@router.post("/models/request")
async def request_model(req: ModelRequest, user: dict = Depends(get_current_user)):
    title = "MODEL_REQUEST"
    msg = f"name={req.name}; link={req.link or ''}; reason={req.reason}; from={user['user']}"
    admin = user_manager.users.get("admin")
    if admin:
        admin.notifications.append({"title": title, "message": msg, "date": str(datetime.datetime.now())})
        user_manager.save_users()
    audit_logger.log("MODEL_REQUEST", msg, user["user"])
    return {"status": "success"}


# --- WebSocket ---

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Determine API Key. 
    # Since frontend currently doesn't send authentication, we use a default key.
    api_key = settings.client_api_key 
    
    await websocket.accept()
    
    # Register with monitor_hub for orchestration updates
    monitor_hub.register(api_key, websocket)
    
    # Also register with client_manager for monitoring stats
    client_host = websocket.client.host
    user_agent = websocket.headers.get("user-agent", "Unknown")
    client_manager.register_client(client_id, client_host, user_agent)
    
    try:
        while True:
            # Keep connection alive and listen for any client messages
            try:
                # Wait for messages (keepalive or commands) with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except:
                    pass
                    
                client_manager.update_activity(client_id)
            except asyncio.TimeoutError:
                # Just a heartbeat check
                pass
                
    except WebSocketDisconnect:
        monitor_hub.unregister(api_key, websocket)
        client_manager.disconnect_client(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        monitor_hub.unregister(api_key, websocket)
        client_manager.disconnect_client(client_id)

@router.post("/clients/{client_id}/kick", dependencies=[Depends(verify_api_key)])
async def kick_client(client_id: str):
    client_manager.kick_client(client_id)
    audit_logger.log("KICK_CLIENT", f"Kicked client {client_id}")
    return {"status": "success", "message": "Client marked for disconnection"}

@router.post("/clients/{client_id}/notify", dependencies=[Depends(verify_api_key)])
async def notify_client(client_id: str, message: str):
    # In a real app, we'd send this via the websocket to that specific client
    # For now, we'll just log it as implemented
    audit_logger.log("NOTIFY_CLIENT", f"Sent message to {client_id}: {message}")
    return {"status": "success", "message": "Notification queued"}

# --- Extended User Management (Admin) ---

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    expiration: Optional[str] = None

class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None
    expiration: Optional[str] = None

class BatchUserRequest(BaseModel):
    usernames: List[str]
    action: str # enable, disable, delete

class CreateGuestRequest(BaseModel):
    duration_hours: int = 24

@router.post("/admin/users/create")
async def admin_create_user(data: CreateUserRequest, user: dict = Depends(get_current_admin)):
    success = user_manager.create_user(data.username, data.password, data.role, data.expiration)
    if not success:
        raise HTTPException(status_code=400, detail="User already exists or failed to create")
    audit_logger.log("ADMIN_CREATE_USER", f"Created user {data.username}", user["user"])
    return {"status": "success"}

@router.put("/admin/users/{username}")
async def admin_update_user(username: str, data: UpdateUserRequest, user: dict = Depends(get_current_admin)):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        return {"status": "success", "message": "No changes"}
    
    if not user_manager.update_user(username, updates):
        raise HTTPException(status_code=404, detail="User not found")
    
    audit_logger.log("ADMIN_UPDATE_USER", f"Updated user {username}: {updates}", user["user"])
    return {"status": "success"}

@router.delete("/admin/users/{username}")
async def admin_delete_user(username: str, user: dict = Depends(get_current_admin)):
    if not user_manager.delete_user(username):
        raise HTTPException(status_code=400, detail="Failed to delete user")
    audit_logger.log("ADMIN_DELETE_USER", f"Deleted user {username}", user["user"])
    return {"status": "success"}

@router.post("/admin/users/batch")
async def admin_batch_users(data: BatchUserRequest, user: dict = Depends(get_current_admin)):
    count = 0
    for username in data.usernames:
        if data.action == "enable":
            if user_manager.update_user(username, {"status": "active"}): count += 1
        elif data.action == "disable":
            if user_manager.update_user(username, {"status": "rejected"}): count += 1
        elif data.action == "delete":
            if user_manager.delete_user(username): count += 1
            
    audit_logger.log("ADMIN_BATCH_ACTION", f"Batch {data.action} on {len(data.usernames)} users", user["user"])
    return {"status": "success", "processed": count}

@router.post("/admin/guests")
async def create_guest(data: CreateGuestRequest, user: dict = Depends(get_current_admin)):
    import datetime
    username = f"guest_{secrets.token_hex(4)}"
    password = secrets.token_hex(6)
    expiration = (datetime.datetime.now() + datetime.timedelta(hours=data.duration_hours)).isoformat()
    
    user_manager.create_user(username, password, "guest", expiration)
    audit_logger.log("ADMIN_CREATE_GUEST", f"Created guest {username}", user["user"])
    return {"status": "success", "username": username, "password": password, "expiration": expiration}

# --- Personal User Management ---

class UpdateProfileRequest(BaseModel):
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.get("/user/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    u = user_manager.users.get(user["user"])
    if not u: raise HTTPException(status_code=404, detail="User not found")
    return u.model_dump(exclude={"password_hash", "client_secret", "client_id"})

@router.put("/user/profile")
async def update_profile(data: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    user_manager.update_profile(user["user"], updates)
    audit_logger.log("USER_UPDATE_PROFILE", "User updated profile", user["user"])
    return {"status": "success"}

@router.post("/user/password")
async def change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    u = user_manager.users.get(user["user"])
    # Verify old password
    if u.password_hash != hashlib.sha256(data.old_password.encode()).hexdigest():
         raise HTTPException(status_code=400, detail="Invalid old password")
         
    if not user_manager.change_password(user["user"], data.new_password):
        raise HTTPException(status_code=400, detail="Failed to change password (check policy)")
        
    audit_logger.log("USER_CHANGE_PASSWORD", "User changed password", user["user"])
    return {"status": "success"}

@router.post("/user/2fa/toggle")
async def toggle_2fa(enable: bool, user: dict = Depends(get_current_user)):
    user_manager.update_user(user["user"], {"is_2fa_enabled": enable})
    audit_logger.log("USER_2FA_TOGGLE", f"2FA set to {enable}", user["user"])
    return {"status": "success", "enabled": enable}

@router.get("/user/export")
async def export_data(user: dict = Depends(get_current_user)):
    u = user_manager.users.get(user["user"])
    if not u: raise HTTPException(status_code=404)
    audit_logger.log("USER_EXPORT_DATA", "User exported data", user["user"])
    return u.model_dump(exclude={"password_hash"})

@router.get("/user/history")
async def get_history(user: dict = Depends(get_current_user)):
    u = user_manager.users.get(user["user"])
    if not u: raise HTTPException(status_code=404)
    return u.history
