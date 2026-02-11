import uuid
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Event(BaseModel):
    """
    Standard CloudEvent-like structure for internal communication.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str # Routing Key
    type: str  # e.g., "agent.task.created", "agent.log"
    source: str  # e.g., "orchestrator", "agent:coder-1"
    time: float = Field(default_factory=time.time)
    data: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
