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

class MonitorHub:
    def __init__(self):
        self.connections: Dict[str, List] = {}
        self.started = False
        self.broadcasting = False

    async def start(self):
        if not self.started:
            message_bus.subscribe("broadcast", self._handle_bus_event)
            message_bus.subscribe("monitor", self._handle_bus_event)
            self.started = True

    async def start_broadcasting(self):
        """Start periodic system stats broadcast."""
        if self.broadcasting:
            return
        self.broadcasting = True
        asyncio.create_task(self._broadcast_loop())

    async def _broadcast_loop(self):
        while self.broadcasting:
            try:
                stats = monitor.get_system_stats()
                model_info = monitor.get_model_info()
                
                msg = {
                    "type": "system_stats",
                    "data": {
                        "system": stats,
                        "model": model_info,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                }
                
                # Broadcast to all admin/dashboard connections
                # Assuming 'admin' role or just broadcast to all for now as per dashboard logic
                await self.broadcast("all", "admin", msg)
                
            except Exception as e:
                logger.error(f"Broadcast loop error: {e}")
            
            await asyncio.sleep(2) # Update every 2 seconds

    async def _handle_bus_event(self, event: Event):
        """Handle events from MessageBus and forward to WebSockets."""
        data = event.data
        api_key = data.get("api_key") or data.get("user_id")
        # If explicit api_key is provided in data, send to that user
        # Otherwise, treat as broadcast if event.topic is 'broadcast'
        
        # Mapping Event to Frontend Message Format
        msg = {
            "type": data.get("type", event.type),
            "timestamp": datetime.datetime.fromtimestamp(event.time).isoformat(),
            "data": data
        }
        
        # Flatten data fields for compatibility with existing frontend
        # Existing frontend expects: type, status, project_id, message, etc. at top level
        # So we merge data into msg
        msg.update(data)
        
        if api_key:
            await self.broadcast(api_key, "user", msg)
        elif event.topic == "broadcast":
            await self.broadcast("all", "admin", msg)

    async def broadcast(self, api_key: str, role: str, message: dict):
        message["timestamp"] = message.get("timestamp") or datetime.datetime.now().isoformat()
        targets = []
        if role == "admin":
            # Flatten all lists of connections
            targets = [ws for sublist in self.connections.values() for ws in sublist]
        else:
            targets = self.connections.get(api_key, [])
        
        dead_connections = []
        for ws in list(targets): # Iterate over copy
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)
        
        for ws in dead_connections:
            self._remove_dead_connection(ws)

    def _remove_dead_connection(self, ws):
        # Efficiently remove ws from wherever it is
        for key, conns in list(self.connections.items()):
            if ws in conns:
                conns.remove(ws)
                if not conns:
                    del self.connections[key]

    def register(self, api_key: str, ws):
        self.connections.setdefault(api_key, []).append(ws)

    def unregister(self, api_key: str, ws):
        if api_key in self.connections:
            try:
                if ws in self.connections[api_key]:
                    self.connections[api_key].remove(ws)
                if not self.connections[api_key]:
                    del self.connections[api_key]
            except ValueError:
                pass

monitor_hub = MonitorHub()

class ClientManager:
    def __init__(self):
        self.clients: Dict[str, dict] = {}

    def register_client(self, session_id: str, ip: str, user_agent: str):
        self.clients[session_id] = {"ip": ip, "user_agent": user_agent, "last_seen": datetime.datetime.now().isoformat()}

    def update_activity(self, session_id: str):
        if session_id in self.clients:
            self.clients[session_id]["last_seen"] = datetime.datetime.now().isoformat()

    def get_clients(self):
        return self.clients

    def disconnect_client(self, session_id: str):
        if session_id in self.clients:
            del self.clients[session_id]

client_manager = ClientManager()

class Monitor:
    def get_system_stats(self):
        try:
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=None)
            return {
                "cpu_percent": cpu_percent,
                "memory_used_gb": round(mem.used / (1024**3), 2),
                "memory_total_gb": round(mem.total / (1024**3), 2),
                "memory_percent": mem.percent
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"cpu_percent": 0, "memory_percent": 0, "memory_used_gb": 0, "memory_total_gb": 0}

    def get_model_info(self):
        status = getattr(llm_engine, "status", "unknown")
        return {
            "status": status,
            "model_name": settings.model_path.split("/")[-1] if settings.model_path else "Unknown",
            "context_window": settings.n_ctx
        }

    def get_clients(self):
        return client_manager.clients
    def get_settings_summary(self):
        return {}

class AuditLogger:
    def log(self, action: str, details: str, user: str = ""):
        pass

monitor = Monitor()
audit_logger = AuditLogger()
