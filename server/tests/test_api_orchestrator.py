
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from server.app import app
from server.core.projects import projects_store
from server.middleware.auth import verify_api_key
from server.routers.dashboard import get_current_user

# Override Auth
def override_verify_api_key():
    return "test-key"

def override_get_current_user():
    return {"user": "test_user", "role": "admin"}

app.dependency_overrides[verify_api_key] = override_verify_api_key
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def mock_llm():
    with patch("server.core.llm.llm_engine") as mock:
        mock.generate_response.return_value = "Mock Response"
        yield mock

def test_init_team():
    with patch("server.core.projects.projects_store.projects", {}), \
         patch("server.core.projects.projects_store.save"):
        
        pid = "proj-test"
        projects_store.projects[pid] = {"id": pid, "name": "Test Project", "owner_key": "test-key", "agents": []}
        
        headers = {"X-API-Key": "test-key"}
        response = client.post(f"/api/v1/projects/{pid}/init_team", headers=headers)
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        agents = projects_store.projects[pid]["agents"]
        assert len(agents) == 4
        assert agents[0]["role_name"] == "Product Manager"

def test_orchestrate_endpoint(mock_llm):
    with patch("server.core.projects.projects_store.projects", {}), \
         patch("server.core.projects.projects_store.save"):
         
        pid = "proj-test"
        projects_store.projects[pid] = {
            "id": pid, 
            "name": "Test Project", 
            "owner_key": "test-key", 
            "agents": [
                {"role_name": "Product Manager", "model_name": "test-model", "system_prompt": "You are PM"},
                {"role_name": "Coder", "model_name": "test-model", "system_prompt": "You are Coder"}
            ]
        }
        
        plan_json = """
        [
            {"title": "Step 1", "content": "Do it", "target_role": "Coder"}
        ]
        """
        # Orchestrator calls: 
        # 1. Plan (LLM)
        # 2. Execute Step 1 (LLM)
        # 3. Report (LLM)
        mock_llm.generate_response.side_effect = [plan_json, "Code Done", "Report"]
        
        headers = {"X-API-Key": "test-key"}
        payload = {"message": "Build a website"}
        
        response = client.post(f"/api/v1/projects/{pid}/orchestrate", json=payload, headers=headers)
        
        if response.status_code != 200:
            print(response.json())
            
        assert response.status_code == 200
        data = response.json()
        assert "outputs" in data
        assert "report" in data
