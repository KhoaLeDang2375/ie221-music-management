"""[NGƯỜI A] Kiểm thử cho nhóm API Quản trị tài khoản (UC-16)."""

from fastapi.testclient import TestClient


def test_list_users_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/users")
    assert response.status_code == 401


def test_list_users_forbidden_for_normal_user(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/users", headers=user_headers)
    assert response.status_code == 403


def test_list_users_as_admin_and_filter_role(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    res_all = client.get("/api/v1/users?page=1&page_size=10", headers=admin_headers)
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["page"] == 1
    assert data_all["page_size"] == 10
    assert data_all["total"] >= 1
    assert len(data_all["items"]) <= 10

    res_admin = client.get("/api/v1/users?role=admin", headers=admin_headers)
    assert res_admin.status_code == 200
    items_admin = res_admin.json()["items"]
    assert len(items_admin) >= 1
    assert all(user["role"] == "admin" for user in items_admin)


def test_get_user_by_id_success(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/users/2", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 2
    assert data["username"] == "testuser"
    assert "password_hash" not in data


def test_get_user_by_id_not_found(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/users/999999", headers=admin_headers)
    assert response.status_code == 404


def test_update_other_user_role_and_status_success(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.put(
        "/api/v1/users/2",
        headers=admin_headers,
        json={"role": "admin", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 2
    assert data["role"] == "admin"
    assert data["is_active"] is False


def test_update_user_not_found(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.put(
        "/api/v1/users/999999",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert response.status_code == 404


def test_admin_cannot_self_lock_or_demote(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    res_lock = client.put(
        "/api/v1/users/1",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert res_lock.status_code == 409

    res_demote = client.put(
        "/api/v1/users/1",
        headers=admin_headers,
        json={"role": "user"},
    )
    assert res_demote.status_code == 409
