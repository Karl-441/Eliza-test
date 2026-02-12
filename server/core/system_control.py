import pyautogui
import subprocess
import psutil
import logging
from typing import List, Dict, Optional
from .config import settings

logger = logging.getLogger(__name__)

# Safety Failsafe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class SystemController:
    def __init__(self):
        self.whitelist: List[str] = settings.allowed_apps
        
    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """Safely move mouse to coordinates."""
        try:
            screen_w, screen_h = pyautogui.size()
            
            # Clamp coordinates
            x = max(0, min(x, screen_w - 1))
            y = max(0, min(y, screen_h - 1))
            
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            logger.error(f"Mouse move error: {e}")
            return False

    def click_mouse(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left'):
        try:
            pyautogui.click(x=x, y=y, button=button)
            return True
        except Exception as e:
            logger.error(f"Mouse click error: {e}")
            return False
            
    def type_text(self, text: str):
        try:
            pyautogui.write(text)
            return True
        except Exception as e:
            logger.error(f"Keyboard error: {e}")
            return False
            
    def launch_app(self, app_name: str):
        """Launch an application if it is in the whitelist."""
        # Simple fuzzy match or exact match
        target = None
        
        # Check if full path provided and whitelisted
        if app_name in self.whitelist:
            target = app_name
        else:
            # Check just the executable name
            for allowed in self.whitelist:
                if app_name.lower() in allowed.lower():
                    target = allowed
                    break
        
        if not target:
            logger.warning(f"Blocked attempt to launch unauthorized app: {app_name}")
            return False
            
        try:
            subprocess.Popen(target)
            return True
        except Exception as e:
            logger.error(f"Launch error: {e}")
            return False
            
    def get_running_processes(self) -> List[Dict[str, str]]:
        """Get list of running processes (top 20 by memory usage)."""
        procs = []
        try:
            for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    p.info['memory_percent'] = round(p.info['memory_percent'], 2)
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass
            
        # Sort by memory usage
        procs.sort(key=lambda x: x['memory_percent'], reverse=True)
        return procs[:20]

system_controller = SystemController()
