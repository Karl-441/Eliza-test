import pytest
from fastapi.testclient import TestClient
from server.app import app
from server.core.users import user_manager
import datetime

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_users():
    user_manager.users = {}
    user_manager.create_default_admin()
    user_manager.create_user("test_user", "Pass123", "user")

def test_admin_user_management():
    # Login as admin
    login_res = client.post("/api/v1/dashboard/login", json={"username": "admin", "password": "admin"})
    cookies = login_res.cookies

    # 1. Create User
    create_res = client.post("/api/v1/dashboard/admin/users/create", json={
        "username": "new_guy", "password": "Pass123", "role": "user"
    }, cookies=cookies)
    assert create_res.status_code == 200
    assert "new_guy" in user_manager.users

    # 2. Update User
    update_res = client.put("/api/v1/dashboard/admin/users/new_guy", json={
        "role": "admin"
    }, cookies=cookies)
    assert update_res.status_code == 200
    assert user_manager.users["new_guy"].role == "admin"

    # 3. Batch Action (Disable)
    batch_res = client.post("/api/v1/dashboard/admin/users/batch", json={
        "usernames": ["new_guy", "test_user"], "action": "disable"
    }, cookies=cookies)
    assert batch_res.status_code == 200
    assert user_manager.users["new_guy"].status == "rejected"
    assert user_manager.users["test_user"].status == "rejected"

    # 4. Create Guest
    guest_res = client.post("/api/v1/dashboard/admin/guests", json={"duration_hours": 1}, cookies=cookies)
    assert guest_res.status_code == 200
    data = guest_res.json()
    assert data["username"].startswith("guest_")
    assert user_manager.users[data["username"]].expiration is not None

def test_user_profile_management():
    # Login as user
    login_res = client.post("/api/v1/dashboard/login", json={"username": "test_user", "password": "Pass123"})
    cookies = login_res.cookies

    # 1. Get Profile
    prof_res = client.get("/api/v1/dashboard/user/profile", cookies=cookies)
    assert prof_res.status_code == 200
    assert prof_res.json()["username"] == "test_user"

    # 2. Update Profile
    upd_res = client.put("/api/v1/dashboard/user/profile", json={
        "email": "test@example.com"
    }, cookies=cookies)
    assert upd_res.status_code == 200
    assert user_manager.users["test_user"].profile["email"] == "test@example.com"

    # 3. Change Password
    pw_res = client.post("/api/v1/dashboard/user/password", json={
        "old_password": "Pass123", "new_password": "NewPass123"
    }, cookies=cookies)
    assert pw_res.status_code == 200
    
    # Verify new password login
    new_login = client.post("/api/v1/dashboard/login", json={"username": "test_user", "password": "NewPass123"})
    assert new_login.status_code == 200

    # 4. Toggle 2FA
    tfa_res = client.post("/api/v1/dashboard/user/2fa/toggle?enable=true", cookies=cookies)
    assert tfa_res.status_code == 200
    assert user_manager.users["test_user"].is_2fa_enabled is True

    # 5. Get History
    hist_res = client.get("/api/v1/dashboard/user/history", cookies=cookies)
    assert hist_res.status_code == 200
    logs = hist_res.json()
    assert len(logs) > 0
    assert any(l["action"] == "PASSWORD_CHANGED" for l in logs)

if __name__ == "__main__":
    try:
        test_admin_user_management()
        print("test_admin_user_management PASSED")
        test_user_profile_management()
        print("test_user_profile_management PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
