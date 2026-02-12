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
        self.load_persona()

    def load_persona(self):
        if "persona" in memory_manager.user_profile:
            try:
                self.current_persona = PersonaModel(**memory_manager.user_profile["persona"])
            except Exception as e:
                logger.error(f"Failed to load persona: {e}")

    def save_persona(self):
        memory_manager.update_profile("persona", self.current_persona.dict())

    def analyze_memory(self):
        """
        Analyzes LTM to extract persona traits using LLM.
        """
        from .llm import llm_engine
        
        ltm = memory_manager.long_term_memory
        if not ltm:
            return
            
        # Limit analysis to last 50 user messages to save context/time
        user_msgs = [n.content for n in ltm if n.role == "user"][-50:]
        if not user_msgs:
            return
            
        text_corpus = "\n".join(user_msgs)
        
        prompt = f"""
        Analyze the following user messages to extract their persona profile.
        
        User Messages:
        {text_corpus}
        
        Return a JSON object with the following fields:
        - interests: list of strings (e.g. ["coding", "sci-fi"])
        - communication_style: string (one of: formal, casual, terse, verbose)
        - traits: dictionary of string keys and float values 0.0-1.0 (e.g. {{"analytical": 0.8, "creative": 0.4}})
        
        Output JSON only.
        """
        
        try:
            response = llm_engine.generate_completion([{"role": "user", "content": prompt}])
            
            # Simple parsing of JSON from response (handling potential markdown code blocks)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            data = json.loads(response.strip())
            
            self.current_persona.interests = data.get("interests", [])
            self.current_persona.communication_style = data.get("communication_style", "formal")
            self.current_persona.traits = data.get("traits", {})
            
            # Relationship Level (based on interaction count)
            count = len(ltm) + len(memory_manager.short_term_memory)
            self.current_persona.relationship_level = min(100, count * 2)
            
            import datetime
            self.current_persona.last_analyzed = datetime.datetime.now().isoformat()
            self.save_persona()
            logger.info("Persona analysis complete (LLM based).")
            
        except Exception as e:
            logger.error(f"Failed to analyze persona with LLM: {e}")

    def get_persona(self) -> Dict[str, Any]:
        return self.current_persona.dict()

persona_manager = PersonaManager()
