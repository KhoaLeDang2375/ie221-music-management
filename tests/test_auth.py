"""[NGƯỜI A] Kiểm thử cho nhóm API Auth (UC-01, UC-02, UC-05)."""
from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.session import engine
from app.deps import get_db
from app.main import app
@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Tạo TestClient dùng DB transaction tự rollback sau mỗi test case."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    def override_get_db() -> Generator[Session, None, None]:
        yield session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()
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