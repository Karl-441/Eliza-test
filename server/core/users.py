import json
import os
from pathlib import Path
import hashlib
import secrets
import logging
import re
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from .config import settings
import datetime

logger = logging.getLogger(__name__)

class User(BaseModel):
    username: str
    password_hash: str
    role: str = "guest" # admin, user, guest
    status: str = "pending" # pending, active, rejected
    client_name: str = ""
    client_id: str = ""
    client_secret: str = ""
    created_at: str
    last_login: str = ""
    notifications: List[Dict[str, str]] = Field(default_factory=list)
    failed_login_attempts: int = 0
    lockout_until: Optional[str] = None
    profile: Dict[str, str] = Field(default_factory=dict) # avatar, email, phone
    tts_preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "voice_id": "default",
        "speed": 100,
        "pitch": 0,
        "volume": 100,
        "language": "zh"
    })
    is_2fa_enabled: bool = False
    expiration: Optional[str] = None # For guest accounts
    history: List[Dict[str, str]] = Field(default_factory=list) # action, date, details

class UserManager:
    def __init__(self, db_path=None):
        base_dir = Path(__file__).resolve().parent.parent
        data_path = base_dir / "data" / "users.json" if db_path is None else Path(db_path)
        self.db_path = str(data_path)
        self.users: Dict[str, User] = {}
        self.load_users()

    def load_users(self):
        if not os.path.exists(self.db_path):
            # Create default admin
            self.create_default_admin()
            return
        
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for u in data:
                    # Backward compatibility handling
                    if "status" not in u: u["status"] = "active"
                    if "client_name" not in u: u["client_name"] = "Default"
                    if "client_id" not in u: u["client_id"] = ""
                    if "client_secret" not in u: u["client_secret"] = ""
                    if "notifications" not in u: u["notifications"] = []
                    if "failed_login_attempts" not in u: u["failed_login_attempts"] = 0
                    if "lockout_until" not in u: u["lockout_until"] = None
                    if "profile" not in u: u["profile"] = {}
                    if "tts_preferences" not in u: u["tts_preferences"] = {
                        "voice_id": "default", "speed": 100, "pitch": 0, "volume": 100, "language": "zh"
                    }
                    if "is_2fa_enabled" not in u: u["is_2fa_enabled"] = False
                    if "expiration" not in u: u["expiration"] = None
                    if "history" not in u: u["history"] = []
                    self.users[u["username"]] = User(**u)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.create_default_admin()

    def save_users(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([u.dict() for u in self.users.values()], f, indent=4)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def create_default_admin(self):
        # Only if no users exist or forced
        if "admin" not in self.users:
            # Default password "admin" -> sha256
            pw_hash = hashlib.sha256("admin".encode()).hexdigest()
            import datetime
            self.users["admin"] = User(
                username="admin", 
                password_hash=pw_hash, 
                role="admin", 
                status="active",
                client_name="System Admin",
                created_at=datetime.datetime.now().isoformat()
            )
            self.save_users()

    def validate_password(self, password: str) -> bool:
        if len(password) < 8: return False
        if not re.search(r"[A-Z]", password): return False
        if not re.search(r"[a-z]", password): return False
        if not re.search(r"\d", password): return False
        return True

    def register_user(self, username, password, client_name) -> tuple[bool, str]:
        if username in self.users:
            return False, "Username already exists"
        
        if not self.validate_password(password):
            return False, "Password must be at least 8 chars, contain uppercase, lowercase and number"

        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        import datetime
        
        self.users[username] = User(
            username=username,
            password_hash=pw_hash,
            role="user",
            status="pending",
            client_name=client_name,
            created_at=datetime.datetime.now().isoformat()
        )
        self.save_users()
        return True, "Registration pending approval"

    def approve_user(self, username) -> Optional[User]:
        if username not in self.users:
            return None
        
        user = self.users[username]
        user.status = "active"
        user.client_id = secrets.token_hex(8)
        user.client_secret = secrets.token_hex(32)
        
        # Add notification
        user.notifications.append({
            "title": "Account Approved",
            "message": f"Your account has been approved. Client ID: {user.client_id}, Client Secret: {user.client_secret}",
            "date": datetime.datetime.now().isoformat()
        })
        
        self.save_users()
        return user

    def reject_user(self, username):
        if username in self.users:
            self.users[username].status = "rejected"
            self.save_users()

    def get_api_keys(self) -> set:
        # Collect all active client_secrets
        keys = set()
        keys.add("eliza-client-key-12345") 
        for u in self.users.values():
            if u.status == "active" and u.client_secret:
                keys.add(u.client_secret)
        return keys

    def authenticate(self, username, password) -> Optional[User]:
        user = self.users.get(username)
        if not user:
            return None
        
        # Check lockout
        if user.lockout_until:
            try:
                lockout_time = datetime.datetime.fromisoformat(user.lockout_until)
                if datetime.datetime.now() < lockout_time:
                    logger.warning(f"User {username} is locked out until {user.lockout_until}")
                    return None
                else:
                    # Lockout expired
                    user.lockout_until = None
                    user.failed_login_attempts = 0
            except ValueError:
                # Handle invalid date format if corrupted
                user.lockout_until = None
                user.failed_login_attempts = 0
        
        # Check expiration
        if user.expiration:
            try:
                exp_time = datetime.datetime.fromisoformat(user.expiration)
                if datetime.datetime.now() > exp_time:
                    logger.info(f"User {username} expired at {user.expiration}")
                    return None
            except ValueError:
                pass # Ignore bad date format

        # Check status
        if user.status != "active":
            return None

        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash == pw_hash:
            user.last_login = datetime.datetime.now().isoformat()
            user.failed_login_attempts = 0
            user.lockout_until = None
            self.save_users()
            return user
        else:
            # Failed login
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # Lockout for 15 minutes
                user.lockout_until = (datetime.datetime.now() + datetime.timedelta(minutes=15)).isoformat()
            self.save_users()
            return None
    
    # ... (rest of methods)

    def create_user(self, username, password, role="user", expiration=None) -> bool:
        # Admin manual creation
        if username in self.users:
            return False
        
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        import datetime
        self.users[username] = User(
            username=username,
            password_hash=pw_hash,
            role=role,
            status="active",
            client_name="Manual Created",
            client_id=secrets.token_hex(8),
            client_secret=secrets.token_hex(32),
            created_at=datetime.datetime.now().isoformat(),
            expiration=expiration
        )
        self.log_history(username, "ACCOUNT_CREATED", f"Account created with role {role}")
        self.save_users()
        return True

    def update_user(self, username, updates: dict) -> bool:
        if username not in self.users: return False
        user = self.users[username]
        
        for k, v in updates.items():
            if hasattr(user, k):
                setattr(user, k, v)
        
        self.log_history(username, "ACCOUNT_UPDATED", f"Updated fields: {list(updates.keys())}")
        self.save_users()
        return True

    def update_profile(self, username, profile_data: dict) -> bool:
        if username not in self.users: return False
        user = self.users[username]
        user.profile.update(profile_data)
        self.log_history(username, "PROFILE_UPDATED", "Profile details updated")
        self.save_users()
        return True

    def update_tts_preferences(self, username, prefs: dict) -> bool:
        if username not in self.users: return False
        user = self.users[username]
        # Merge updates
        user.tts_preferences.update(prefs)
        self.log_history(username, "TTS_PREF_UPDATED", "TTS preferences updated")
        self.save_users()
        return True

    def change_password(self, username, new_password) -> bool:
        if username not in self.users: return False
        if not self.validate_password(new_password): return False
        
        user = self.users[username]
        user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.log_history(username, "PASSWORD_CHANGED", "Password changed successfully")
        self.save_users()
        return True

    def log_history(self, username, action, details):
        if username in self.users:
            import datetime
            self.users[username].history.append({
                "action": action,
                "details": details,
                "date": datetime.datetime.now().isoformat()
            })
            # Keep history manageable
            if len(self.users[username].history) > 50:
                self.users[username].history = self.users[username].history[-50:]

    def delete_user(self, username) -> bool:
        if username == "admin": 
            return False 
        if username in self.users:
            del self.users[username]
            self.save_users()
            return True
        return False

    def list_users(self) -> List[dict]:
        return [u.dict(exclude={"password_hash"}) for u in self.users.values()]

user_manager = UserManager()
