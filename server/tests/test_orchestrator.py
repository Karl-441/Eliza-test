import asyncio
import json
from unittest.mock import MagicMock, patch
import pytest
import sys

# Ensure we can import server modules
import os
sys.path.append(os.getcwd())

from server.core import orchestrator

@pytest.mark.asyncio
async def test_orchestrate_flow():
    # Mock dependencies
    orchestrator.llm_engine = MagicMock()
    orchestrator.projects_store = MagicMock()
    orchestrator.monitor_hub = MagicMock()
    orchestrator.user_manager = MagicMock()
    
    # Mock projects_store.list_agents
    orchestrator.projects_store.list_agents.return_value = {
        "agents": [
            {"role_name": "Coder", "model_name": "model-a"},
            {"role_name": "Tester", "model_name": "model-b"}
        ]
    }
    
    # Mock monitor_hub.broadcast to be async
    async def async_mock(*args, **kwargs):
        pass
    orchestrator.monitor_hub.broadcast = MagicMock(side_effect=async_mock)
    
    # Mock user_manager
    mock_user = MagicMock()
    mock_user.role = "admin"
    mock_user.client_secret = "key-123"
    orchestrator.user_manager.users = {"u1": mock_user}

    # Mock decompose response
    mock_json_response = json.dumps([
        {"title": "Step 1", "content": "Do A", "target_role": "Coder"},
        {"title": "Step 2", "content": "Do B", "target_role": "Tester"}
    ])
    
    # Configure LLM side effects
    # 1. decompose_tasks -> returns JSON
    # 2. Step 1 execution
    # 3. Step 2 execution
    # 4. Final report
    orchestrator.llm_engine.generate_response.side_effect = [
        mock_json_response, 
        "Code for Step 1", 
        "Test for Step 2", 
        "Final Report"
    ]
        
    result = await orchestrator.orchestrate("proj-123", "Build a feature", "key-123")
    
    assert len(result["outputs"]) == 2
    assert result["outputs"][0]["role"] == "Coder"
    assert result["outputs"][0]["content"] == "Code for Step 1"
    assert result["outputs"][1]["role"] == "Tester"
    assert result["outputs"][1]["content"] == "Test for Step 2"
    assert result["report"] == "Final Report"
    
    print("Orchestration Test Passed!")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_orchestrate_flow())
