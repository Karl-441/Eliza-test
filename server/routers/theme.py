from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from server.core.i18n import I18N

router = APIRouter(prefix="/api/v1/theme", tags=["theme"])

class ThemeColors(BaseModel):
    background_primary: str
    background_secondary: str
    background_tertiary: str
    accent_primary: str
    accent_hover: str
    accent_dim: str
    accent_warn: str
    accent_danger: str
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_inverse: str
    border: str
    grid: str

class ThemeConfig(BaseModel):
    name: str
    version: str
    dark_mode: bool
    colors: ThemeColors
    fonts: Dict[str, str]
    spacing: Dict[str, int]
    assets: Dict[str, str]

# Default Tactical Theme (GFL Style)
DEFAULT_THEME = {
    "name": "Tactical Default",
    "version": "1.0.0",
    "dark_mode": True,
    "colors": {
        "background_primary": "#141414",
        "background_secondary": "#1F1F1F",
        "background_tertiary": "#252525",
        "accent_primary": "#FFB400",
        "accent_hover": "#FFD700",
        "accent_dim": "rgba(255, 180, 0, 0.3)",
        "accent_warn": "#FF5500",
        "accent_danger": "#FF0000",
        "text_primary": "#E0E0E0",
        "text_secondary": "#909090",
        "text_disabled": "#505050",
        "text_inverse": "#000000",
        "border": "#404040",
        "grid": "rgba(255, 255, 255, 0.05)"
    },
    "fonts": {
        "family_main": '"Segoe UI", "Roboto", "Orbitron", sans-serif',
        "family_mono": '"JetBrains Mono", "Consolas", monospace'
    },
    "spacing": {
        "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32
    },
    "assets": {
        "logo_griffin": "/static/assets/griffin_logo.png",
        "logo_sf": "/static/assets/sf_logo.jpg",
        "bg_particle_color": "#FFB400"
    }
}

@router.get("/config", response_model=ThemeConfig)
async def get_theme_config():
    """Get the current active theme configuration."""
    # Return copy with localized name
    theme = DEFAULT_THEME.copy()
    theme["name"] = I18N.t("theme_name_default")
    return theme

@router.get("/checksum")
async def get_theme_checksum():
    """Get checksum of current theme for consistency validation."""
    import hashlib
    import json
    
    theme_str = json.dumps(DEFAULT_THEME, sort_keys=True)
    return {"checksum": hashlib.sha256(theme_str.encode()).hexdigest(), "version": DEFAULT_THEME["version"]}
