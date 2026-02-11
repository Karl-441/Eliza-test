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

# Global session store
# project_id -> { "orchestrator": Agent, "workers": [Agent] }
active_sessions: Dict[str, Dict] = {}
_monitor_subscribed = False

async def stop_session(project_id: str):
    session = active_sessions.pop(project_id, None)
    if session:
        if session.get("orchestrator"):
            await session["orchestrator"].stop()
        for a in session.get("workers", []):
            await a.stop()
        print(f"Session for project {project_id} stopped.")

async def delayed_stop_session(project_id: str):
    await asyncio.sleep(5) # Give time for final messages to flush
    await stop_session(project_id)

async def global_monitor_handler(event: Event):
    if event.type == "orchestration.status":
        project_id = event.data.get("project_id")
        status = event.data.get("status")
        
        if project_id and project_id in active_sessions:
            # Check for terminal states
            if status in ["complete", "failed", "cancelled", "rejected"]: 
                # Note: "rejected" means approval rejected. Should we stop?
                # Logic in OrchestratorAgent:
                # if rejected -> status="failed", sends "rejected" event.
                # So "rejected" event is sent, then it might stay alive?
                # OrchestratorAgent.handle_approval(False) -> status="failed" -> send "rejected".
                # Then it saves state.
                # It does NOT send "complete".
                # So we should treat "rejected" as terminal?
                # Or "failed" as terminal?
                # Let's check OrchestratorAgent again.
                # handle_approval(False) -> status="failed".
                # It doesn't call finish_workflow.
                
                # So we should probably listen for "rejected" too.
                # Or just check if status is "failed" or "complete".
                # The event data status is "rejected".
                asyncio.create_task(delayed_stop_session(project_id))

async def orchestrate(project_id: str, message: str, api_key: str) -> Dict[str, any]:
    """
    Refactored Orchestration Entry Point.
    Uses MessageBus and Agents.
    Non-blocking: Starts the workflow and returns immediately.
    """
    global _monitor_subscribed
    
    # 1. Ensure Infrastructure is running
    message_bus.start()
    await monitor_hub.start()
    
    if not _monitor_subscribed:
        message_bus.subscribe("monitor", global_monitor_handler)
        _monitor_subscribed = True

    # 2. Cleanup existing session
    if project_id in active_sessions:
        await stop_session(project_id)

    # 3. Load Project Agents Metadata
    agents_data = projects_store.list_agents(project_id).get("agents", [])
    
    # 4. Spin up runtime Agents (Temporary for this session)
    active_agents: List[GenericLLMAgent] = []
    
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

    # 5. Create Orchestrator Agent
    orchestrator_agent = OrchestratorAgent(
        agent_id=f"orch-{uuid.uuid4().hex[:4]}",
        project_id=project_id,
        api_key=api_key,
        agents_metadata=agents_data
    )
    await orchestrator_agent.start()

    # 6. Register Session
    active_sessions[project_id] = {
        "orchestrator": orchestrator_agent,
        "workers": active_agents
    }

    # 7. Trigger Workflow
    correlation_id = str(uuid.uuid4())
    
    # Send directly to orchestrator agent
    await orchestrator_agent.send_event(
        target_topic=f"agent.{orchestrator_agent.id}",
        type="orchestration.start",
        data={"message": message, "project_id": project_id},
        correlation_id=correlation_id
    )
            
    return {"status": "started", "project_id": project_id, "workflow_id": orchestrator_agent.workflow_id}

