import time
from typing import Dict, List, Optional
from pydantic import BaseModel

class AgentInfo(BaseModel):
    id: str
    role: str
    status: str = "offline"  # online, offline, busy, error
    capabilities: List[str] = []
    last_heartbeat: float = 0.0
    meta: Dict = {}

class ServiceRegistry:
    """
    Service Discovery and Health Check Registry.
    """
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._ttl = 30.0  # seconds

    def register(self, agent: AgentInfo):
        self._agents[agent.id] = agent
        agent.last_heartbeat = time.time()
        agent.status = "online"

    def heartbeat(self, agent_id: str):
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = time.time()
            self._agents[agent_id].status = "online"

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    def find_agents_by_role(self, role: str) -> List[AgentInfo]:
        self._prune_dead_agents()
        return [a for a in self._agents.values() if a.role == role and a.status == "online"]

    def _prune_dead_agents(self):
        now = time.time()
        for aid, agent in self._agents.items():
            if now - agent.last_heartbeat > self._ttl:
                agent.status = "offline"

# Global Singleton
registry = ServiceRegistry()
