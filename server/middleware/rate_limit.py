from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from server.core.i18n import I18N

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Identify client by API Key or IP
        client_id = request.headers.get("X-API-Key") or request.client.host
        
        current_time = time.time()
        
        # Clean up old requests
        self.request_counts[client_id] = [
            t for t in self.request_counts[client_id] 
            if t > current_time - self.window_seconds
        ]
        
        if len(self.request_counts[client_id]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": I18N.t("error_rate_limit_exceeded")}
            )
            
        self.request_counts[client_id].append(current_time)
        
        response = await call_next(request)
        return response
