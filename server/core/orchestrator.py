import json
import re
import uuid
from typing import List, Dict, Optional
import datetime
import asyncio
from .projects import projects_store
from .llm import llm_engine
from .monitor import monitor_hub
from .users import user_manager
from .tools import get_tool_descriptions, execute_tool
from ..core.i18n import I18N
from server.core.framework.bus import message_bus
from server.core.framework.events import Event
from server.core.framework.agents import GenericLLMAgent, OrchestratorAgent

async def orchestrate(project_id: str, message: str, api_key: str) -> Dict[str, any]:
    """
    Refactored Orchestration Entry Point.
    Uses MessageBus and Agents.
    """
    
    # 1. Ensure Infrastructure is running
    message_bus.start()
    await monitor_hub.start()

    # 2. Load Project Agents Metadata
    agents_data = projects_store.list_agents(project_id).get("agents", [])
    
    # 3. Spin up runtime Agents (Temporary for this session)
    active_agents: List[GenericLLMAgent] = []
    
    # Check if we already have agents running? 
    # For now, we create fresh ones for simplicity (stateless)
    for a in agents_data:
        agent = GenericLLMAgent(
            agent_id=f"{a['role_name']}-{uuid.uuid4().hex[:4]}",
            role=a['role_name'],
            model_name=a.get("model_name", "server-qwen2.5-7b"),
            system_prompt=a.get("description", f"You are {a['role_name']}"),
            project_id=project_id
        )
        await agent.start()
        active_agents.append(agent)

    # 4. Create Orchestrator Agent
    orchestrator_agent = OrchestratorAgent(
        agent_id=f"orch-{uuid.uuid4().hex[:4]}",
        project_id=project_id,
        api_key=api_key,
        agents_metadata=agents_data
    )
    await orchestrator_agent.start()

    # 5. Listen for Completion
    # We create a Future that resolves when orchestration is complete
    loop = asyncio.get_running_loop()
    completion_future = loop.create_future()

    # OrchestratorAgent publishes to 'monitor' topic with status 'complete'.
    async def monitor_handler(event: Event):
        if event.type == "orchestration.status" and event.data.get("status") == "complete" and event.data.get("project_id") == project_id:
             if not completion_future.done():
                completion_future.set_result(event.data)
    
    message_bus.subscribe("monitor", monitor_handler)

    # 6. Trigger Workflow
    correlation_id = str(uuid.uuid4())
    await message_bus.publish(Event(
        topic="orchestration.start", # OrchestratorAgent listens to this (via process_message or custom)
        # Wait, OrchestratorAgent.process_message handles "orchestration.start" type
        # But BaseAgent listens to "agent.{id}" and "broadcast".
        # We need to send to orchestrator directly or broadcast.
        # OrchestratorAgent doesn't subscribe to "orchestration.start" topic by default.
        # BaseAgent subscribes to "broadcast", "agent.{id}", "role.{role}".
        # OrchestratorAgent role is "admin".
        # Let's use direct message to agent ID, or broadcast.
        # But we want to trigger *this* specific orchestrator.
        # Actually, OrchestratorAgent subscribes to "orchestration.start" ?? No.
        
        # Let's fix OrchestratorAgent subscription in agents.py if needed.
        # BaseAgent subscribes to: "broadcast", "agent.{id}", "role.{role}".
        # So we send to "agent.{orchestrator_agent.id}"
        
        type="orchestration.start",
        source="api",
        data={"message": message, "project_id": project_id},
        correlation_id=correlation_id
    ))
    
    # Wait, OrchestratorAgent.process_message needs to handle "orchestration.start".
    # BaseAgent._handle_direct calls process_message.
    # So sending to agent.{id} works.
    
    await orchestrator_agent.send_event(
        target_topic=f"agent.{orchestrator_agent.id}",
        type="orchestration.start",
        data={"message": message},
        correlation_id=correlation_id
    )

    # 7. Wait
    try:
        result = await asyncio.wait_for(completion_future, timeout=300) # 5 min timeout
    except asyncio.TimeoutError:
        result = {"error": "Orchestration timed out"}
    finally:
        # Cleanup
        await orchestrator_agent.stop()
        for a in active_agents:
            await a.stop()
            
    return result
