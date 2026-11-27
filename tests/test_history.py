"""[NGƯỜI B] Kiểm thử cho nhóm API Lịch sử nghe nhạc (UC-13)."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import engine
from app.deps import get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Tạo TestClient dùng DB transaction savepoint tự rollback sau mỗi test case.

    Returns:
        Generator trả về đối tượng TestClient của FastAPI.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

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
    """Đăng nhập và trả về header Authorization Bearer.

    Args:
        client: Đối tượng TestClient dùng gọi API login.
        username: Tên đăng nhập.
        password: Mật khẩu gốc.

    Returns:
        Dictionary chứa header Authorization với Bearer JWT token.
    """
    res = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_history_requires_authentication(client: TestClient) -> None:
    """Kiểm tra chưa đăng nhập sẽ bị chặn 401 ở cả GET và POST lịch sử."""
    assert client.get("/api/v1/me/history").status_code == 401
    assert client.post("/api/v1/me/history", json={"track_id": 1}).status_code == 401


def test_get_recent_history_default_and_limit_validation(client: TestClient) -> None:
    """Kiểm tra mặc định trả 20 bài gần nhất đúng thứ tự giảm dần và chặn limit ngoài 1..50."""
    user_headers = _get_auth_headers(client, "testuser", "testuser@123")

    res = client.get("/api/v1/me/history", headers=user_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 20
    assert all(item["user_id"] == 2 for item in items)
    assert all("track" in item and item["track"]["name"] for item in items)
    timestamps = [item["listened_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)

    res_5 = client.get("/api/v1/me/history?limit=5", headers=user_headers)
    assert res_5.status_code == 200
    assert len(res_5.json()) == 5

    assert client.get("/api/v1/me/history?limit=0", headers=user_headers).status_code == 422
    assert client.get("/api/v1/me/history?limit=51", headers=user_headers).status_code == 422


def test_record_listen_repeated_and_nonexistent_track(client: TestClient) -> None:
    """Kiểm tra ghi nhận nghe lặp lại 1 bài nhiều lần và báo 404 khi bài không tồn tại."""
    user_headers = _get_auth_headers(client, "testuser", "testuser@123")

    assert (
        client.post(
            "/api/v1/me/history", headers=user_headers, json={"track_id": 999999}
        ).status_code
        == 404
    )

    first = client.post("/api/v1/me/history", headers=user_headers, json={"track_id": 5})
    assert first.status_code == 201
    assert first.json()["track_id"] == 5

    second = client.post("/api/v1/me/history", headers=user_headers, json={"track_id": 5})
    assert second.status_code == 201
    assert second.json()["history_id"] != first.json()["history_id"]

    recent = client.get("/api/v1/me/history?limit=2", headers=user_headers)
    assert recent.status_code == 200
    assert [item["history_id"] for item in recent.json()] == [
        second.json()["history_id"],
        first.json()["history_id"],
    ]
