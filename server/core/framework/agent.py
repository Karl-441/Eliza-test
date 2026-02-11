import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from .events import Event
from .bus import message_bus
from .registry import registry, AgentInfo

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, description: str = ""):
        self.id = agent_id
        self.role = role
        self.description = description
        self.running = False
        self._heartbeat_task = None

    async def start(self):
        """Register and start listening."""
        self.running = True
        
        # Register
        info = AgentInfo(id=self.id, role=self.role, meta={"desc": self.description})
        registry.register(info)
        
        # Subscribe to general broadcasts and direct messages
        message_bus.subscribe("broadcast", self._handle_broadcast)
        message_bus.subscribe(f"agent.{self.id}", self._handle_direct)
        message_bus.subscribe(f"role.{self.role}", self._handle_role_task)
        
        # Start Heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Agent {self.id} ({self.role}) started.")
        
        await self.on_start()

    async def stop(self):
        self.running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        logger.info(f"Agent {self.id} stopped.")
        await self.on_stop()

    async def _heartbeat_loop(self):
        while self.running:
            registry.heartbeat(self.id)
            await asyncio.sleep(10)

    # --- Event Handlers ---

    async def _handle_broadcast(self, event: Event):
        """Handle system-wide broadcasts."""
        pass

    async def _handle_direct(self, event: Event):
        """Handle messages sent specifically to this agent ID."""
        await self.process_message(event)

    async def _handle_role_task(self, event: Event):
        """Handle messages sent to this agent's role (Load Balancing could be added here)."""
        await self.process_task(event)

    # --- Abstract Methods ---

    @abstractmethod
    async def process_message(self, event: Event):
        """Process direct messages."""
        pass

    @abstractmethod
    async def process_task(self, event: Event):
        """Process task assignments."""
        pass
        
    async def on_start(self):
        pass
        
    async def on_stop(self):
        pass

    # --- Helper Methods ---
    
    async def send_event(self, target_topic: str, type: str, data: Dict[str, Any], correlation_id: str = None):
        event = Event(
            topic=target_topic,
            type=type,
            source=f"agent:{self.id}",
            data=data,
            correlation_id=correlation_id
        )
        await message_bus.publish(event)
