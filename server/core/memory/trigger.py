from server.core.memory.vector_store import vector_store
from server.core.config import settings
import re
import logging

logger = logging.getLogger(__name__)

class MemoryTrigger:
    def __init__(self):
        self.threshold_instinct = 0.85
        self.threshold_subconscious = 0.7

    def analyze_and_retrieve(self, user_input: str):
        """
        Analyze user input to decide which memory layers to activate and retrieve them.
        Returns a combined context string and detailed results.
        """
        triggers = {
            "instinct": False,
            "subconscious": False,
            "active_recall": False,
            "results": {}
        }
        
        # 1. Search Instinct (High frequency, fast)
        instinct_results = vector_store.search_instinct(user_input, limit=1, threshold=self.threshold_instinct)
        if instinct_results:
            triggers["instinct"] = True
            triggers["results"]["instinct"] = instinct_results
            
        # 2. Search Subconscious (Implicit association)
        subconscious_results = vector_store.search_subconscious(user_input, limit=3, threshold=self.threshold_subconscious)
        if subconscious_results:
            triggers["subconscious"] = True
            triggers["results"]["subconscious"] = subconscious_results
            
        # 3. Active Recall (Explicit intent)
        # Simple heuristic for now, can be upgraded to LLM classification
        if self._is_active_recall_intent(user_input):
            triggers["active_recall"] = True
            active_results = vector_store.search_active_recall(user_input, limit=5)
            triggers["results"]["active_recall"] = active_results
        
        return self._synthesize_context(triggers), triggers

    def _is_active_recall_intent(self, text: str) -> bool:
        # TODO: Use LLM for better intent classification
        patterns = [
            r"remember", r"recall", r"what did i say", r"history", 
            r"last time", r"yesterday", r"before", r"mentioned"
        ]
        combined_pattern = "|".join(patterns)
        return bool(re.search(combined_pattern, text, re.IGNORECASE))

    def _synthesize_context(self, triggers: dict) -> str:
        context_parts = []
        
        results = triggers.get("results", {})
        
        if results.get("instinct"):
            instincts = [r["memory"].content for r in results["instinct"]]
            context_parts.append(f"Instincts: {'; '.join(instincts)}")
            
        if results.get("subconscious"):
            subs = [r["memory"].content for r in results["subconscious"]]
            context_parts.append(f"Subconscious: {'; '.join(subs)}")
            
        if results.get("active_recall"):
            active = [r["memory"].content for r in results["active_recall"]]
            context_parts.append(f"Recalled Events: {'; '.join(active)}")
            
        return "\n".join(context_parts)

memory_trigger = MemoryTrigger()
