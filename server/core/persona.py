import logging
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .memory import memory_manager

logger = logging.getLogger(__name__)

class PersonaModel(BaseModel):
    traits: Dict[str, float] = Field(default_factory=dict)  # e.g., {"openness": 0.8}
    interests: List[str] = Field(default_factory=list)
    communication_style: str = "formal"  # formal, casual, terse, verbose
    relationship_level: int = 0  # 0-100
    last_analyzed: str = ""

class PersonaManager:
    def __init__(self):
        self.current_persona = PersonaModel()
        # In a real app, this would be persisted per user. 
        # For now, we attach it to the MemoryManager's user profile or store it separately.
        self.load_persona()

    def load_persona(self):
        # Try to load from user profile in memory manager
        if "persona" in memory_manager.user_profile:
            try:
                self.current_persona = PersonaModel(**memory_manager.user_profile["persona"])
            except Exception as e:
                logger.error(f"Failed to load persona: {e}")

    def save_persona(self):
        memory_manager.update_profile("persona", self.current_persona.dict())

    def analyze_memory(self):
        """
        Analyzes LTM to extract persona traits.
        This is a heuristic/mock implementation. In production, use LLM.
        """
        ltm = memory_manager.long_term_memory
        if not ltm:
            return

        # Simple keyword heuristics
        text_corpus = " ".join([n.content for n in ltm if n.role == "user"]).lower()
        
        # Interests
        keywords = {
            "tech": ["code", "programming", "computer", "ai", "python", "server"],
            "art": ["design", "color", "music", "draw", "creative"],
            "strategy": ["plan", "tactic", "mission", "objective"],
            "casual": ["haha", "lol", "cool", "yeah", "sup"]
        }
        
        detected_interests = set()
        for category, words in keywords.items():
            if any(w in text_corpus for w in words):
                detected_interests.add(category)
        
        self.current_persona.interests = list(detected_interests)

        # Style
        if "casual" in detected_interests:
            self.current_persona.communication_style = "casual"
        elif len(text_corpus.split()) / (len(ltm) + 1) > 20:
            self.current_persona.communication_style = "verbose"
        else:
            self.current_persona.communication_style = "formal"

        # Relationship Level (based on interaction count)
        count = len(ltm) + len(memory_manager.short_term_memory)
        self.current_persona.relationship_level = min(100, count * 2)

        # Traits (Mock)
        self.current_persona.traits = {
            "analytical": 0.8 if "tech" in detected_interests else 0.4,
            "creative": 0.8 if "art" in detected_interests else 0.3,
            "proactive": 0.6
        }
        
        import datetime
        self.current_persona.last_analyzed = datetime.datetime.now().isoformat()
        self.save_persona()
        logger.info("Persona analysis complete.")

    def get_persona(self) -> Dict[str, Any]:
        return self.current_persona.dict()

persona_manager = PersonaManager()
