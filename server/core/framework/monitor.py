import time
from typing import Dict, Any
from .events import Event
from .bus import message_bus

class SystemMonitor:
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_latency": 0.0
        }
        self.running = False

    async def start(self):
        self.running = True
        message_bus.subscribe("task.*", self._on_task_event)
        message_bus.subscribe("agent.*", self._on_agent_event)

    async def _on_task_event(self, event: Event):
        if event.type.endswith(".created"):
            self.metrics["tasks_total"] += 1
        elif event.type.endswith(".completed"):
            self.metrics["tasks_completed"] += 1
        elif event.type.endswith(".failed"):
            self.metrics["tasks_failed"] += 1

    async def _on_agent_event(self, event: Event):
        # Log agent lifecycle events
        pass

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics

monitor = SystemMonitor()
