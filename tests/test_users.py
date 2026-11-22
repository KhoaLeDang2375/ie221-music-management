"""[NGƯỜI A] Kiểm thử cho nhóm API Quản trị tài khoản (UC-16)."""

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


def _get_auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    """Đăng nhập và trả về header Authorization Bearer."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_users_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/users")
    assert response.status_code == 401


def test_list_users_forbidden_for_normal_user(client: TestClient) -> None:
    headers = _get_auth_headers(client, "testuser", "testuser@123")
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403


def test_list_users_as_admin_and_filter_role(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")

    res_all = client.get("/api/v1/users?page=1&page_size=10", headers=headers)
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["page"] == 1
    assert data_all["page_size"] == 10
    assert data_all["total"] >= 1
    assert len(data_all["items"]) <= 10

    res_admin = client.get("/api/v1/users?role=admin", headers=headers)
    assert res_admin.status_code == 200
    items_admin = res_admin.json()["items"]
    assert len(items_admin) >= 1
    assert all(user["role"] == "admin" for user in items_admin)


def test_get_user_by_id_success(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")
    response = client.get("/api/v1/users/2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 2
    assert data["username"] == "testuser"
    assert "password_hash" not in data


def test_get_user_by_id_not_found(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")
    response = client.get("/api/v1/users/999999", headers=headers)
    assert response.status_code == 404


def test_update_other_user_role_and_status_success(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")
    response = client.put(
        "/api/v1/users/2",
        headers=headers,
        json={"role": "admin", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 2
    assert data["role"] == "admin"
    assert data["is_active"] is False


def test_update_user_not_found(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")
    response = client.put(
        "/api/v1/users/999999",
        headers=headers,
        json={"is_active": False},
    )
    assert response.status_code == 404


def test_admin_cannot_self_lock_or_demote(client: TestClient) -> None:
    headers = _get_auth_headers(client, "admin", "admin@123")

    res_lock = client.put(
        "/api/v1/users/1",
        headers=headers,
        json={"is_active": False},
    )
    assert res_lock.status_code == 409

    res_demote = client.put(
        "/api/v1/users/1",
        headers=headers,
        json={"role": "user"},
    )
    assert res_demote.status_code == 409