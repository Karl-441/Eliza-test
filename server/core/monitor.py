import asyncio
import datetime
from typing import List, Dict
from server.core.framework.bus import message_bus
from server.core.framework.events import Event

class MonitorHub:
    def __init__(self):
        self.connections: Dict[str, List] = {}
        self.started = False

    async def start(self):
        if not self.started:
            message_bus.subscribe("broadcast", self._handle_bus_event)
            message_bus.subscribe("monitor", self._handle_bus_event)
            self.started = True

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
            targets = sum(self.connections.values(), [])
        else:
            targets = self.connections.get(api_key, [])
        for ws in targets:
            try:
                await ws.send_json(message)
            except:
                pass

    def register(self, api_key: str, ws):
        self.connections.setdefault(api_key, []).append(ws)

    def unregister(self, api_key: str, ws):
        if api_key in self.connections:
            try:
                self.connections[api_key].remove(ws)
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
        return {"cpu": 0, "mem": 0, "uptime": 0}
    def get_model_info(self):
        return {"status": "ok"}
    def get_clients(self):
        return client_manager.clients
    def get_settings_summary(self):
        return {}

class AuditLogger:
    def log(self, action: str, details: str, user: str = ""):
        pass

monitor = Monitor()
audit_logger = AuditLogger()
