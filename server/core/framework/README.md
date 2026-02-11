# Multi-Agent Framework Core

This directory contains the refactored core components for the Event-Driven Multi-Agent Architecture.

## Components

- **`events.py`**: Defines the `Event` data structure (CloudEvents compliant).
- **`bus.py`**: The asynchronous `MessageBus` for pub/sub communication.
- **`registry.py`**: `ServiceRegistry` for agent discovery and health monitoring.
- **`agent.py`**: `BaseAgent` class that all specific agents must inherit from.
- **`monitor.py`**: System observability module.

## Usage

```python
from .bus import message_bus
from .agent import BaseAgent

# 1. Start Bus
message_bus.start()

# 2. Define Agent
class MyAgent(BaseAgent):
    async def process_task(self, event):
        print(f"Got task: {event.data}")

# 3. Start Agent
agent = MyAgent("my-agent", "worker")
await agent.start()

# 4. Publish Event
await message_bus.publish(Event(topic="role.worker", type="task.created", ...))
```

## Testing

Run tests via:
```bash
python tests/test_framework.py
```
