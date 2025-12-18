from PyQt5.QtCore import QObject, pyqtSignal
import requests
from ..framework.theme import THEME

class ThemeManager(QObject):
    theme_updated = pyqtSignal()

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.current_checksum = None

    def _headers(self):
        try:
            return getattr(self.client, "_get_headers")()
        except Exception:
            return {"X-API-Key": getattr(self.client, "api_key", "eliza-client-key-12345")}

    def fetch_theme(self):
        url = f"{self.client.base_url}/api/v1/theme/config"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                
                # Transform data to match THEME structure
                colors = data.get("colors", {})
                fonts = data.get("fonts", {})
                spacing = data.get("spacing", {})
                
                theme_data = {
                    "colors": {
                        "background": colors.get("background_primary"),
                        "background_secondary": colors.get("background_secondary"),
                        "background_tertiary": colors.get("background_tertiary"),
                        "accent": colors.get("accent_primary"),
                        "accent_hover": colors.get("accent_hover"),
                        "accent_dim": colors.get("accent_dim"),
                        "text_primary": colors.get("text_primary"),
                        "text_secondary": colors.get("text_secondary"),
                        "border": colors.get("border"),
                        "grid": colors.get("grid"),
                        "success": "#00FF99", # Default if missing
                        "warning": colors.get("accent_warn", "#FF4444"),
                        "error": colors.get("accent_danger", "#FF0000")
                    },
                    "fonts": {
                        "family_main": fonts.get("family_main"),
                        "family_code": fonts.get("family_mono")
                    },
                    "spacing": spacing
                }
                
                # Remove None values
                theme_data["colors"] = {k: v for k, v in theme_data["colors"].items() if v}
                theme_data["fonts"] = {k: v for k, v in theme_data["fonts"].items() if v}
                
                THEME.load_theme(theme_data)
                self.theme_updated.emit()
                return True
        except Exception as e:
            print(f"Theme fetch error: {e}")
        return False

    def check_updates(self):
        try:
            url = f"{self.client.base_url}/api/v1/theme/checksum"
            resp = requests.get(url, headers=self._headers(), timeout=5)
            if resp.status_code != 200:
                return False
            data = resp.json()
            checksum = data.get("checksum")
            if checksum and checksum != self.current_checksum:
                self.current_checksum = checksum
                self.fetch_theme()
            return True
        except Exception:
            return False
