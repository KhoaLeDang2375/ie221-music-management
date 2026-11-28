"""[NGƯỜI A] Kiểm thử cho nhóm API Playlist (UC-06..UC-11, UC-17)."""

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
    res = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_playlist(
    client: TestClient, headers: dict[str, str], name: str = "Nhạc Chạy Bộ"
) -> int:
    res = client.post(
        "/api/v1/playlists",
        headers=headers,
        json={"name": name, "description": "Playlist test"},
    )
    assert res.status_code == 201
    return res.json()["playlist_id"]


def test_create_playlist_success_and_duplicate_conflict(client: TestClient) -> None:
    headers = _get_auth_headers(client, "testuser", "testuser@123")

    res1 = client.post(
        "/api/v1/playlists",
        headers=headers,
        json={"name": "Chill Cuối Tuần", "description": "Nghe thư giãn"},
    )
    assert res1.status_code == 201
    assert res1.json()["name"] == "Chill Cuối Tuần"

    # Trùng tên trong cùng tài khoản -> 409 (BR-05)
    res2 = client.post(
        "/api/v1/playlists",
        headers=headers,
        json={"name": "Chill Cuối Tuần"},
    )
    assert res2.status_code == 409


def test_create_playlist_blank_name(client: TestClient) -> None:
    headers = _get_auth_headers(client, "testuser", "testuser@123")
    res = client.post(
        "/api/v1/playlists",
        headers=headers,
        json={"name": "   "},
    )
    assert res.status_code == 422


def test_list_my_playlists_and_admin_list(client: TestClient) -> None:
    user_headers = _get_auth_headers(client, "testuser", "testuser@123")
    admin_headers = _get_auth_headers(client, "admin", "admin@123")
    _create_playlist(client, user_headers, "My Rock List")

    res_me = client.get("/api/v1/playlists/me", headers=user_headers)
    assert res_me.status_code == 200
    assert any(p["name"] == "My Rock List" for p in res_me.json()["items"])

    # User thường gọi endpoint kiểm duyệt của admin -> 403
    res_forbidden = client.get("/api/v1/playlists", headers=user_headers)
    assert res_forbidden.status_code == 403

    # Admin xem toàn bộ playlist -> 200
    res_admin = client.get("/api/v1/playlists", headers=admin_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["total"] >= 1


def test_playlist_ownership_and_admin_moderation(client: TestClient) -> None:
    owner_headers = _get_auth_headers(client, "testuser", "testuser@123")
    other_headers = _get_auth_headers(client, "luisg", "luisg@123")
    admin_headers = _get_auth_headers(client, "admin", "admin@123")

    playlist_id = _create_playlist(client, owner_headers, "Private List")

    # Người khác xem / sửa / xóa -> 403 (BR-02)
    assert client.get(f"/api/v1/playlists/{playlist_id}", headers=other_headers).status_code == 403
    assert (
        client.put(
            f"/api/v1/playlists/{playlist_id}",
            headers=other_headers,
            json={"name": "Hack Name"},
        ).status_code
        == 403
    )

    # Admin xem được (200) nhưng KHÔNG được sửa nội dung (403 - BR-02)
    assert client.get(f"/api/v1/playlists/{playlist_id}", headers=admin_headers).status_code == 200
    assert (
        client.put(
            f"/api/v1/playlists/{playlist_id}",
            headers=admin_headers,
            json={"name": "Admin Edit"},
        ).status_code
        == 403
    )

    # Chủ sở hữu sửa thành công (200)
    res_update = client.put(
        f"/api/v1/playlists/{playlist_id}",
        headers=owner_headers,
        json={"name": "Renamed List"},
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Renamed List"

    # Admin xóa để kiểm duyệt -> 204 (UC-17)
    assert client.delete(f"/api/v1/playlists/{playlist_id}", headers=admin_headers).status_code == 204


def test_add_and_remove_track_in_playlist(client: TestClient) -> None:
    headers = _get_auth_headers(client, "testuser", "testuser@123")
    playlist_id = _create_playlist(client, headers, "Track Test List")

    # Thêm bài hát hợp lệ (track_id=1 có sẵn trong DB mẫu) -> 201
    res_add = client.post(
        f"/api/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_id": 1},
    )
    assert res_add.status_code == 201

    # Thêm trùng bài hát -> 409 (BR-03)
    res_dup = client.post(
        f"/api/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_id": 1},
    )
    assert res_dup.status_code == 409

    # Thêm track_id không tồn tại -> 422
    res_missing = client.post(
        f"/api/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_id": 999999},
    )
    assert res_missing.status_code == 422

    # Xem chi tiết thấy có 1 bài
    res_detail = client.get(f"/api/v1/playlists/{playlist_id}", headers=headers)
    assert res_detail.status_code == 200
    assert len(res_detail.json()["tracks"]) == 1

    # Gỡ bài hát -> 204
    res_del = client.delete(f"/api/v1/playlists/{playlist_id}/tracks/1", headers=headers)
    assert res_del.status_code == 204