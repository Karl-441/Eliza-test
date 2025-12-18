import pytest
from fastapi.testclient import TestClient
from server.app import app
from server.core.users import user_manager, User
import hashlib

client = TestClient(app)

# Setup mock user manager
def mock_users():
    user_manager.users = {}
    user_manager.create_default_admin()

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    mock_users()
    yield
    mock_users()

def test_registration_flow():
    # 1. Register
    payload = {
        "username": "test_commander",
        "password": "Password123",
        "client_name": "Test Unit"
    }
    response = client.post("/api/v1/dashboard/register", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify pending
    assert "test_commander" in user_manager.users
    assert user_manager.users["test_commander"].status == "pending"

    # 2. Login as Admin
    # Since we can't easily mock cookies in this simple setup without full flow,
    # we'll mock the dependency override or just use the login endpoint to get cookie.
    
    login_payload = {"username": "admin", "password": "admin"}
    login_res = client.post("/api/v1/dashboard/login", json=login_payload)
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # 3. List Users (Admin)
    list_res = client.get("/api/v1/dashboard/admin/users", cookies=cookies)
    assert list_res.status_code == 200
    users = list_res.json()
    assert len(users) >= 2 # admin + test_commander
    target = next(u for u in users if u["username"] == "test_commander")
    assert target["status"] == "pending"

    # 4. Approve User
    approve_res = client.post("/api/v1/dashboard/admin/users/test_commander/approve", cookies=cookies)
    assert approve_res.status_code == 200
    data = approve_res.json()
    assert data["user"]["status"] == "active"
    assert data["user"]["client_id"] is not None
    assert data["user"]["client_secret"] is not None

    # Verify active in DB
    assert user_manager.users["test_commander"].status == "active"

def test_registration_validation():
    # Weak password
    payload = {
        "username": "weak_user",
        "password": "123",
        "client_name": "Test"
    }
    response = client.post("/api/v1/dashboard/register", json=payload)
    assert response.status_code == 400
    assert "Password" in response.json()["detail"]

    # Duplicate user
    user_manager.create_user("dup_user", "Pass123", "user")
    payload["username"] = "dup_user"
    payload["password"] = "Password123"
    response = client.post("/api/v1/dashboard/register", json=payload)
    assert response.status_code == 400
    assert "exists" in response.json()["detail"]

def test_lockout():
    # 1. Register and Approve (or manually create)
    user_manager.create_user("lockout_user", "Pass123", "user")
    
    # 2. Fail login 5 times
    for i in range(5):
        res = client.post("/api/v1/dashboard/login", json={"username": "lockout_user", "password": "WrongPassword"})
        assert res.status_code == 401
    
    # 3. Verify lockout state
    user = user_manager.users["lockout_user"]
    assert user.failed_login_attempts >= 5
    assert user.lockout_until is not None
    
    # 4. Correct password should fail now (locked out)
    res = client.post("/api/v1/dashboard/login", json={"username": "lockout_user", "password": "Pass123"})
    assert res.status_code == 401

def test_notification():
    # 1. Register
    res = client.post("/api/v1/dashboard/register", json={
        "username": "notify_user", "password": "Password123", "client_name": "Notify"
    })
    assert res.status_code == 200
    
    # 2. Approve (Login as admin first)
    login_res = client.post("/api/v1/dashboard/login", json={"username": "admin", "password": "admin"})
    cookies = login_res.cookies
    
    approve_res = client.post("/api/v1/dashboard/admin/users/notify_user/approve", cookies=cookies)
    assert approve_res.status_code == 200
    
    # 3. Check notification in User object
    user = user_manager.users["notify_user"]
    assert len(user.notifications) > 0
    assert "Approved" in user.notifications[0]["title"]
    
    # 4. Check notification endpoint (login as notify_user)
    # Need to get cookies for notify_user
    login_res_user = client.post("/api/v1/dashboard/login", json={"username": "notify_user", "password": "Password123"})
    assert login_res_user.status_code == 200
    user_cookies = login_res_user.cookies
    
    notif_res = client.get("/api/v1/dashboard/notifications", cookies=user_cookies)
    assert notif_res.status_code == 200
    assert len(notif_res.json()) > 0
    assert "Approved" in notif_res.json()[0]["title"]

if __name__ == "__main__":
    # Manually run tests if executed as script
    try:
        test_registration_flow()
        print("test_registration_flow PASSED")
        test_registration_validation()
        print("test_registration_validation PASSED")
        test_lockout()
        print("test_lockout PASSED")
        test_notification()
        print("test_notification PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
