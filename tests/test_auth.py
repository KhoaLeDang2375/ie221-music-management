"""[NGƯỜI A] Kiểm thử cho nhóm API Auth (UC-01, UC-02, UC-05)."""

from fastapi.testclient import TestClient


def test_register_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "new_pytest_user",
            "email": "new_pytest_user@example.com",
            "full_name": "New Pytest User",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_pytest_user"
    assert data["role"] == "user"
    assert "password_hash" not in data


def test_register_ignores_admin_role_br01(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "forced_role_user",
            "email": "forced_role_user@example.com",
            "full_name": "Forced Role User",
            "password": "password123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_register_duplicate_username(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "another_email@example.com",
            "full_name": "Duplicate User",
            "password": "password123",
        },
    )
    assert response.status_code == 409


def test_register_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "short_pwd_user",
            "email": "short@example.com",
            "full_name": "Short Password",
            "password": "123",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testuser@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "manoj.pareek", "password": "manoj.pareek@123"},
    )
    assert response.status_code == 403


def test_get_me_success(client: TestClient) -> None:
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testuser@123"},
    )
    token = login_res.json()["access_token"]
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "testuser"


def test_get_me_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
