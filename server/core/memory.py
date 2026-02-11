import json
import os
from pathlib import Path
import base64
import time
import math
from typing import List, Dict, Any, Optional
from collections import deque
from abc import ABC, abstractmethod
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from .config import settings
from .prompts import prompt_manager
from .i18n import I18N

class MemoryNode:
    """
    Represents a single unit of memory (engram).
    """
    def __init__(self, content: str, role: str, importance: float = 0.5, emotion: Dict[str, float] = None):
        self.id = str(base64.urlsafe_b64encode(os.urandom(6)).decode('utf-8'))
        self.content = content
        self.role = role
        self.timestamp = time.time()
        self.last_accessed = self.timestamp
        self.access_count = 1
        self.importance = importance  # 0.0 to 1.0
        self.emotion = emotion or {"neutral": 1.0}
        self.associations: Dict[str, float] = {}  # {node_id: strength}
        self.decay_rate = 0.05  # Default decay rate

    def update_access(self):
        self.last_accessed = time.time()
        self.access_count += 1
        # Neuroplasticity: Strengthening with use
        self.importance = min(1.0, self.importance * 1.05)

    def get_current_strength(self) -> float:
        """
        Calculate current memory strength based on forgetting curve.
        S = Initial_Strength * e^(-decay_rate * time_elapsed)
        """
        elapsed_hours = (time.time() - self.last_accessed) / 3600
        # Importance acts as initial strength
        return self.importance * math.exp(-self.decay_rate * elapsed_hours)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "emotion": self.emotion,
            "associations": self.associations,
            "access_count": self.access_count
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(data["content"], data["role"], data["importance"], data.get("emotion"))
        node.id = data["id"]
        node.timestamp = data["timestamp"]
        node.associations = data.get("associations", {})
        node.access_count = data.get("access_count", 1)
        return node

class MemoryStorage(ABC):
    @abstractmethod
    def load(self) -> List[MemoryNode]:
        pass

    @abstractmethod
    def save(self, nodes: List[MemoryNode]):
        pass

class JSONEncryptedStorage(MemoryStorage):
    def __init__(self, file_path: str, key_path: str):
        self.file_path = file_path
        self.key_path = key_path
        self.key = self._load_or_generate_key()

    def _load_or_generate_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return f.read()
        else:
            # Generate 32 bytes for AES-256
            key = os.urandom(32)
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)
            return key

    def _encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + ct)

    def _decrypt(self, data: bytes) -> bytes:
        try:
            raw = base64.b64decode(data)
            iv = raw[:16]
            ct = raw[16:]
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ct) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded_data) + unpadder.finalize()
        except Exception as e:
            print(f"Decryption error: {e}")
            return b"[]"

    def load(self) -> List[MemoryNode]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "rb") as f:
                    encrypted = f.read()
                decrypted = self._decrypt(encrypted)
                data = json.loads(decrypted.decode('utf-8'))
                return [MemoryNode.from_dict(item) for item in data]
            except Exception as e:
                print(f"Error loading LTM: {e}")
                return []
        return []

    def save(self, nodes: List[MemoryNode]):
        try:
            data = [node.to_dict() for node in nodes]
            json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
            encrypted = self._encrypt(json_bytes)
            with open(self.file_path, "wb") as f:
                f.write(encrypted)
        except Exception as e:
            print(f"Error saving LTM: {e}")

class MemoryManager:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data"
        
        # Storage Backend
        self.ltm_file = str(data_dir / "long_term_memory.json")
        self.key_file = str(data_dir / "secret.key")
        self.storage = JSONEncryptedStorage(self.ltm_file, self.key_file)

        # 1. Memory Layering
        # Short-term (Working) Memory: High fidelity, limited capacity
        self.stm_capacity = 10
        self.short_term_memory: deque[MemoryNode] = deque(maxlen=self.stm_capacity)
        
        # Long-term Memory: Unlimited capacity, decay-based retrieval
        self.long_term_memory: List[MemoryNode] = self.storage.load()
        
        # Legacy support (for API compatibility)
        self.history = deque(maxlen=20) 
        
        self.is_paused = False
        self.user_profile: Dict[str, Any] = {}
        
        # Reuse storage key logic for profile for now, or move profile to storage too
        # For minimal refactor, keeping profile logic similar but using storage key helper if needed
        # Actually, let's keep profile logic separate for now as requested "Independent memory database"
        
        self.load_profile()
        self.apply_preferences()

    # Profile logic kept inside MemoryManager for now as it's separate from LTM
    # But uses the same key... duplicating logic slightly or should expose key from storage
    # Let's use the storage's key for profile too if possible, but for safety copy logic or make helper
    # I'll keep the profile logic here but simplified.

    def _encrypt(self, data: bytes) -> bytes:
        return self.storage._encrypt(data)

    def _decrypt(self, data: bytes) -> bytes:
        return self.storage._decrypt(data)

    def save_ltm(self):
        self.storage.save(self.long_term_memory)

    def add_message(self, role: str, content: str):
        if self.is_paused:
            return

        # 1. Create Memory Node
        # Heuristic importance: User messages slightly more important initially
        importance = 0.6 if role == "user" else 0.4
        
        # 3. Emotional Tagging (Placeholder - could use LLM to classify later)
        # Simple keyword heuristic for demo
        emotion = {"neutral": 1.0}
        if "error" in content.lower() or "fail" in content.lower():
            emotion = {"frustration": 0.8}
        elif "good" in content.lower() or "thanks" in content.lower():
            emotion = {"joy": 0.6}
            
        node = MemoryNode(content, role, importance, emotion)
        decay_pref = float(self.user_profile.get("preferences", {}).get("memory_decay_rate", 0.05))
        node.decay_rate = max(0.001, min(0.2, decay_pref))
        
        # 2. Add to Short Term Memory
        self.short_term_memory.append(node)
        self.history.append({"role": role, "content": content}) # Legacy
        
        # 5. Verification & Consolidation
        # Periodically move important STM items to LTM
        self.consolidate_memory(node)
        
        # 4. Associative Linking
        # Link to recent nodes in STM
        if len(self.short_term_memory) > 1:
            prev_node = self.short_term_memory[-2]
            # Heuristic link strength based on temporal proximity
            node.associations[prev_node.id] = 0.8
            prev_node.associations[node.id] = 0.8

    def consolidate_memory(self, node: MemoryNode):
        """
        Move significant memories to LTM.
        """
        # Threshold for consolidation
        if node.importance > 0.3: 
            self.long_term_memory.append(node)
            self.save_ltm()

    def retrieve(self, query: str, limit: int = 5) -> List[MemoryNode]:
        """
        Hybrid retrieval using configurable weights: Semantic, Recency, Primacy, Emotion, Strength
        """
        candidates = []
        
        # Simple Keyword/Semantic Matching (Simulated)
        import re
        query_tokens = set(re.findall(r'\w+', query.lower()))
        
        current_time = time.time()
        weights = self.user_profile.get("preferences", {})
        w_sem = float(weights.get("semantic_weight", 0.6))
        w_rec = float(weights.get("recency_weight", 0.3))
        w_pri = float(weights.get("primacy_weight", 0.2))
        w_em = float(weights.get("emotion_weight", 0.2))
        w_str = 0.3
        
        for node in self.long_term_memory:
            # 1. Activation based on Recency & Decay (Forgetting Curve)
            strength = node.get_current_strength()
            
            # 2. Semantic Match
            node_tokens = set(re.findall(r'\w+', node.content.lower()))
            overlap = len(query_tokens.intersection(node_tokens))
            semantic_score = overlap / (len(query_tokens) + 1) if query_tokens else 0
            
            # 3. Emotional Weighting
            # Emotional memories are recalled easier
            emotion_boost = sum(v for k,v in node.emotion.items() if k != "neutral") * w_em
            recency = max(0.0, 1.0 - ((current_time - node.timestamp) / (3600 * 48)))
            primacy = 1.0 / (1.0 + node.access_count)
            
            # Total Activation Score
            activation = (strength * w_str) + (semantic_score * w_sem) + (recency * w_rec) + (primacy * w_pri) + emotion_boost
            
            if activation > 0.1:
                candidates.append((activation, node))
                
        # Sort by activation
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # 6. Neuroplasticity: Update access for retrieved items
        results = [node for _, node in candidates[:limit]]
        for node in results:
            node.update_access()
            
        return results

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def export_history(self) -> str:
        lines = []
        for msg in self.history:
            timestamp = msg.get("timestamp", "")
            lines.append(f"[{msg['role'].upper()}] {timestamp}: {msg['content']}")
        return "\n".join(lines)

    def get_history(self) -> List[Dict[str, str]]:
        return list(self.history)

    def clear_history(self):
        self.history.clear()
        self.short_term_memory.clear()

    def load_profile(self):
        if os.path.exists(settings.user_profile_path):
            try:
                with open(settings.user_profile_path, "rb") as f:
                    encrypted_data = f.read()
                
                # Check if it's JSON (migration) or Encrypted
                if encrypted_data.strip().startswith(b"{"):
                    try:
                        self.user_profile = json.loads(encrypted_data.decode('utf-8'))
                        # Auto-encrypt on next save
                        self.save_profile()
                    except:
                         pass
                else:
                    decrypted_json = self._decrypt(encrypted_data)
                    self.user_profile = json.loads(decrypted_json.decode('utf-8'))
            except Exception as e:
                print(f"Error loading profile: {e}")
                self.user_profile = {}
        else:
            self.user_profile = {
                "name": "Commander",
                "preferences": {
                    "speech_speed": 1.0,
                    "voice_id": "default",
                    "style": "formal",
                    "theme": "dark",
                    "shortcuts": {}
                }
            }
            self.save_profile()

        # Ensure all keys exist
        defaults = {
            "name": "Commander",
            "preferences": {
                "speech_speed": 1.0,
                "voice_id": "default",
                "style": "formal",
                "theme": "dark",
                "shortcuts": {}
            }
        }
        # Deep merge defaults
        for k, v in defaults.items():
            if k not in self.user_profile:
                self.user_profile[k] = v
            elif isinstance(v, dict) and isinstance(self.user_profile[k], dict):
                for sub_k, sub_v in v.items():
                    if sub_k not in self.user_profile[k]:
                        self.user_profile[k][sub_k] = sub_v

    def save_profile(self):
        os.makedirs(os.path.dirname(settings.user_profile_path), exist_ok=True)
        json_bytes = json.dumps(self.user_profile, ensure_ascii=False).encode('utf-8')
        encrypted_data = self._encrypt(json_bytes)
        with open(settings.user_profile_path, "wb") as f:
            f.write(encrypted_data)

    def update_profile(self, key: str, value: Any):
        # Support nested updates for preferences
        if key.startswith("preferences."):
            pref_key = key.split(".")[1]
            if "preferences" not in self.user_profile:
                self.user_profile["preferences"] = {}
            self.user_profile["preferences"][pref_key] = value
        else:
            self.user_profile[key] = value
        self.save_profile()
        self.apply_preferences()

    def import_profile(self, profile_data: Dict[str, Any]):
        self.user_profile.update(profile_data)
        self.save_profile()
        self.apply_preferences()

    def export_profile_json(self) -> str:
        return json.dumps(self.user_profile, ensure_ascii=False, indent=2)

    def analyze_context(self, current_input: str, limit: int = 3) -> str:
        """
        Advanced context association using LTM retrieval.
        """
        # Retrieve from LTM using new algorithm
        relevant_nodes = self.retrieve(current_input, limit)
        
        if not relevant_nodes:
            return ""
            
        context_str = f"{I18N.t('memory_relevant_past')}\n"
        for node in relevant_nodes:
            # Format timestamp nicely
            ts_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(node.timestamp))
            context_str += f"- [{ts_str}] {node.role}: {node.content}\n"
            
        return context_str

    def apply_preferences(self):
        prefs = self.user_profile.get("preferences", {})
        new_stm = int(prefs.get("stm_capacity", self.stm_capacity))
        new_stm = max(5, min(100, new_stm))
        if new_stm != self.stm_capacity:
            self.stm_capacity = new_stm
            old = list(self.short_term_memory)
            self.short_term_memory = deque(maxlen=self.stm_capacity)
            for item in old[-self.stm_capacity:]:
                self.short_term_memory.append(item)

    def get_context_prompt(self) -> str:
        # Get raw template
        raw_prompt = prompt_manager.get_active_prompt()
        
        # Fill variables
        name = self.user_profile.get("name", "Commander")
        style = self.user_profile.get("preferences", {}).get("style", "formal")
        
        try:
            return raw_prompt.format(name=name, style=style)
        except Exception:
            return raw_prompt # Fallback if formatting fails

memory_manager = MemoryManager()
