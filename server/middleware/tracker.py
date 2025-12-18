from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from server.core.monitor import client_manager

class ClientTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract Client Session ID
        session_id = request.headers.get("X-Client-Session-ID")
        
        if session_id:
            # Check if known
            if session_id in client_manager.clients:
                client_manager.update_activity(session_id)
            else:
                # Register new client
                # Use X-Forwarded-For if behind proxy, else client.host
                ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("User-Agent", "Unknown")
                
                # Filter out Dashboard/Browser connections if they don't have the specific ID?
                # The Dashboard uses WebSocket, so it's handled separately.
                # Here we handle REST clients (Eliza Desktop).
                
                client_manager.register_client(session_id, ip, user_agent)
                
        response = await call_next(request)
        return response
