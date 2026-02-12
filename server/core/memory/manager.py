from server.core.memory_legacy import memory_manager as legacy_manager
from server.core.memory.vector_store import vector_store
from server.core.memory.trigger import memory_trigger
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.legacy = legacy_manager

    @property
    def user_profile(self):
        return self.legacy.user_profile

    def update_profile(self, key, value):
        if key in ["personality", "traits", "preferences"]:
            try:
                # Store as instinct memory
                vector_store.add_instinct(f"{key}: {value}", trait_type=key)
            except Exception as e:
                logger.error(f"Failed to add instinct memory: {e}")
        self.legacy.update_profile(key, value)

    def export_profile_json(self):
        return self.legacy.export_profile_json()

    def import_profile(self, data):
        self.legacy.import_profile(data)

    def clear_history(self):
        self.legacy.clear_history()
        # Note: We don't clear vector store to preserve long-term memory
        # unless explicitly requested.

    def add_message(self, role: str, content: str):
        self.legacy.add_message(role, content)
        try:
            vector_store.add_active_recall(content, role)
        except Exception as e:
            logger.error(f"Failed to add active recall memory: {e}")

    def get_context_prompt(self) -> str:
        return self.legacy.get_context_prompt()

    def analyze_context(self, user_input: str) -> str:
        try:
            context, _ = memory_trigger.analyze_and_retrieve(user_input)
            return context
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return ""

    def get_history(self):
        return self.legacy.get_history()

memory_manager = MemoryManager()
