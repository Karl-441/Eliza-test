from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

from server.core.config import settings
from server.middleware.auth import LoggingMiddleware, verify_api_key
from server.middleware.rate_limit import RateLimitMiddleware
from server.middleware.tracker import ClientTrackingMiddleware
from server.routers import system, chat, audio, profile, config, dashboard as dashboard_router, tts_config, theme, search as search_router

# Create FastAPI App with Versioning
app = FastAPI(
    title="Eliza AI Server",
    description="Tactical AI Assistant Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 1. Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ClientTrackingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set strict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Static Files (Dashboard) - Keeping as requested for independent deployment option
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

@app.get("/dashboard", tags=["System"])
async def dashboard():
    dashboard_path = STATIC_DIR / "dashboard.html"
    if not dashboard_path.exists():
        return {"error": "Dashboard file not found"}
    return FileResponse(dashboard_path)

from fastapi import Depends

API_PREFIX = "/api/v1"

app.include_router(system.router, prefix=API_PREFIX + "/system", tags=["System"])
app.include_router(chat.router, prefix=API_PREFIX + "/chat", tags=["Chat"], dependencies=[Depends(verify_api_key)])
app.include_router(audio.router, prefix=API_PREFIX + "/audio", tags=["Audio"], dependencies=[Depends(verify_api_key)])
app.include_router(profile.router, prefix=API_PREFIX + "/profile", tags=["Profile"], dependencies=[Depends(verify_api_key)])
app.include_router(config.router, prefix=API_PREFIX + "/config", tags=["Config"], dependencies=[Depends(verify_api_key)])
app.include_router(tts_config.router, prefix=API_PREFIX + "/tts", tags=["TTS Configuration"])
app.include_router(theme.router, prefix=API_PREFIX + "/theme", tags=["Theme"])
app.include_router(dashboard_router.router, prefix=API_PREFIX + "/dashboard", tags=["Dashboard"])
app.include_router(search_router.router, prefix=API_PREFIX, tags=["Search"])

@app.get("/", tags=["Root"])
def root():
    return {"status": "online", "version": "1.0.0", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
