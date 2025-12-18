from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from server.core.users import user_manager

# Simple API Key Auth
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    # Skip auth for docs and static
    # But since this is a dependency, we use it in routers
    
    # Get active keys from user_manager (dynamic)
    valid_keys = user_manager.get_api_keys()
    
    if not api_key or api_key not in valid_keys:
        # For development ease, if no key provided, maybe allow? 
        # The prompt says "Strict interface authentication".
        # So we reject.
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logging.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        return response
