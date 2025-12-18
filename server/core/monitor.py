import psutil
import time
import logging
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from .config import settings
from .llm import llm_engine

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ClientSession:
    id: str
    ip: str
    connected_at: str
    last_active: str
    user_agent: str = "Unknown"
    status: str = "active"

class AuditLogger:
    def __init__(self, log_file=None):
        base_dir = Path(__file__).resolve().parent.parent
        target = base_dir / "data" / "audit.log" if log_file is None else Path(log_file)
        self.log_file = str(target)
        target.parent.mkdir(parents=True, exist_ok=True)

    def log(self, action: str, details: str, user_ip: str = "system"):
        timestamp = datetime.datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "ip": user_ip
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

class ClientManager:
    def __init__(self):
        self.clients: Dict[str, ClientSession] = {}
        self.audit = AuditLogger()

    def register_client(self, client_id: str, ip: str, user_agent: str):
        now = datetime.datetime.now().isoformat()
        session = ClientSession(
            id=client_id,
            ip=ip,
            connected_at=now,
            last_active=now,
            user_agent=user_agent
        )
        self.clients[client_id] = session
        self.audit.log("CLIENT_CONNECT", f"Client {client_id} connected", ip)
        return session

    def update_activity(self, client_id: str):
        if client_id in self.clients:
            self.clients[client_id].last_active = datetime.datetime.now().isoformat()
            self.clients[client_id].status = "active"

    def disconnect_client(self, client_id: str):
        if client_id in self.clients:
            ip = self.clients[client_id].ip
            del self.clients[client_id]
            self.audit.log("CLIENT_DISCONNECT", f"Client {client_id} disconnected", ip)

    def get_clients(self) -> List[Dict[str, Any]]:
        # Clean up stale clients (optional, but good practice)
        return [asdict(c) for c in self.clients.values()]

    def kick_client(self, client_id: str):
        # In a real WS scenario, we would close the socket.
        # Here we just mark for removal/tracking.
        # The router will handle the actual socket closure if possible.
        self.disconnect_client(client_id)

class SystemMonitor:
    def get_system_stats(self):
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=None)
        
        return {
            "cpu_percent": cpu_percent,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "memory_percent": mem.percent
        }

    def get_model_info(self):
        # Use new status fields from LLMEngine
        status = getattr(llm_engine, "status", "unknown")
        last_error = getattr(llm_engine, "last_error", None)
        
        info = {
            "name": settings.model_path.split("/")[-1] if settings.model_path else "Unknown",
            "status": status,
            "error": last_error,
            "path": settings.model_path,
            "context_window": settings.n_ctx,
            "threads": settings.n_threads,
            "loaded_at": getattr(llm_engine, "loaded_at", None)
        }
        
        if status == "ready" and llm_engine.model:
            # Try to get memory info if possible (llama-cpp-python doesn't expose it easily directly, use process info)
            process = psutil.Process()
            info["process_memory_gb"] = round(process.memory_info().rss / (1024**3), 2)
            
        return info

    def get_settings_summary(self):
        return {
            "time_settings": {
                "timezone": str(time.tzname),
                "system_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "tts_settings": {
                "enabled": settings.enable_audio,
                "api_url": settings.tts_api_url,
                "voices": list(settings.voice_presets.keys())
            }
        }

monitor = SystemMonitor()
client_manager = ClientManager()
audit_logger = AuditLogger()
