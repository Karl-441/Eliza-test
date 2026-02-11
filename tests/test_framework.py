import asyncio
import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.core.framework.bus import message_bus
from server.core.framework.events import Event
from server.core.framework.registry import registry
from server.core.framework.example_agent import LLMAgent

@pytest.mark.asyncio
async def test_agent_workflow():
    # 1. Start Bus
    message_bus.start()
    
    # 2. Create and Start Agent
    agent = LLMAgent("test-agent-1", "tester", "mock-model", "You are a tester.")
    await agent.start()
    
    # Verify Registry
    reg_agent = registry.get_agent("test-agent-1")
    assert reg_agent is not None
    assert reg_agent.status == "online"
    
    # 3. Create a mock orchestrator listener
    received_events = []
    async def orchestrator_handler(event: Event):
        received_events.append(event)
    
    message_bus.subscribe("orchestrator", orchestrator_handler)
    
    # 4. Send Task
    print("Sending task...")
    task_event = Event(
        topic="role.tester",
        type="task.created",
        source="orchestrator",
        data={"task_id": "task-1", "content": "Test this code"},
        correlation_id="corr-1"
    )
    await message_bus.publish(task_event)
    
    # 5. Wait for processing
    print("Waiting for processing...")
    for i in range(5):
        await asyncio.sleep(1)
        print(f"Waited {i+1}s, received: {len(received_events)}")
        if len(received_events) >= 2:
            break
            
    print(f"Total received: {[e.type for e in received_events]}")
    
    # 6. Verify Results
    assert len(received_events) >= 2 # started + completed
    
    started = next((e for e in received_events if e.type == "task.started"), None)
    completed = next((e for e in received_events if e.type == "task.completed"), None)
    
    assert started is not None
    assert completed is not None
    assert completed.data["task_id"] == "task-1"
    assert "Mock Output" in completed.data["output"]
    assert completed.correlation_id == "corr-1"
    
    # 7. Cleanup
    await agent.stop()
    await message_bus.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_agent_workflow())
    print("Test Passed!")
