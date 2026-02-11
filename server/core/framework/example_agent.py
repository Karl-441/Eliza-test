import asyncio
from .agent import BaseAgent
from .events import Event
from .bus import message_bus
from server.core.llm import llm_engine

class LLMAgent(BaseAgent):
    def __init__(self, agent_id: str, role: str, model_name: str, system_prompt: str):
        super().__init__(agent_id, role)
        self.model_name = model_name
        self.system_prompt = system_prompt

    async def process_task(self, event: Event):
        task_content = event.data.get("content")
        task_id = event.data.get("task_id")
        
        # Notify Start
        await self.send_event(f"orchestrator", "task.started", {"task_id": task_id})
        
        try:
            # Simulate LLM call
            prompt = f"{self.system_prompt}\n\nTask: {task_content}"
            # In real scenario: response = await llm_engine.generate_response(prompt)
            response = f"[Mock Output from {self.role}] Processed: {task_content[:20]}..."
            await asyncio.sleep(1) # Simulate latency
            
            # Notify Success
            await self.send_event(f"orchestrator", "task.completed", {
                "task_id": task_id,
                "output": response,
                "agent_id": self.id
            }, correlation_id=event.correlation_id)
            
        except Exception as e:
            await self.send_event(f"orchestrator", "task.failed", {
                "task_id": task_id,
                "error": str(e)
            }, correlation_id=event.correlation_id)

    async def process_message(self, event: Event):
        # Handle direct chat messages
        pass
