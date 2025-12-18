from fastapi.testclient import TestClient
from server.app import app
import pytest

client = TestClient(app)

# API Key for tests
HEADERS = {"X-API-Key": "eliza-client-key-12345"}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_system_status():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "llm" in data
    assert "tts" in data

def test_chat_endpoint():
    payload = {"message": "Hello, Eliza"}
    response = client.post("/api/v1/chat/chat", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)

def test_chat_unauthorized():
    payload = {"message": "Hello"}
    response = client.post("/api/v1/chat/chat", json=payload)
    # Depending on middleware setup, this might be 403 or 422 if dependency fails
    assert response.status_code == 403

def test_voices_endpoint():
    response = client.get("/api/v1/audio/voices", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_profile_endpoint():
    response = client.get("/api/v1/profile/", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
