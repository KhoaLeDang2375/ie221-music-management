"""[NGƯỜI A] Kiểm thử cho nhóm API Playlist (UC-06..UC-11, UC-17)."""

from fastapi.testclient import TestClient

from tests.conftest import get_auth_headers


def test_playlists_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/playlists/me").status_code == 401
    assert client.post("/api/v1/playlists", json={"name": "Test"}).status_code == 401
    assert client.get("/api/v1/playlists/1").status_code == 401
    assert client.put("/api/v1/playlists/1", json={"name": "New"}).status_code == 401
    assert client.delete("/api/v1/playlists/1").status_code == 401
    assert client.post("/api/v1/playlists/1/tracks", json={"track_id": 1}).status_code == 401
    assert client.delete("/api/v1/playlists/1/tracks/1").status_code == 401


def test_playlist_crud_and_tracks_br03_br05(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    assert (
        client.post("/api/v1/playlists", headers=user_headers, json={"name": "   "}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/playlists", headers=user_headers, json={"name": "a" * 101}
        ).status_code
        == 422
    )

    p1 = client.post(
        "/api/v1/playlists",
        headers=user_headers,
        json={"name": "Nhạc Chill Tối", "description": "Nghe thư giãn"},
    )
    assert p1.status_code == 201
    p1_id = p1.json()["playlist_id"]
    assert p1.json()["user_id"] == 2

    # BR-05: Không được trùng tên playlist trong cùng tài khoản
    assert (
        client.post(
            "/api/v1/playlists",
            headers=user_headers,
            json={"name": "nhạc chill tối"},
        ).status_code
        == 409
    )

    p2 = client.post(
        "/api/v1/playlists",
        headers=user_headers,
        json={"name": "Nhạc Tập Gym"},
    )
    assert p2.status_code == 201

    my_list = client.get("/api/v1/playlists/me", headers=user_headers)
    assert my_list.status_code == 200
    assert all(pl["user_id"] == 2 for pl in my_list.json()["items"])
    assert any(pl["playlist_id"] == p1_id for pl in my_list.json()["items"])

    # Đổi tên trùng với playlist khác của mình -> 409; explicit null name -> 422
    assert (
        client.put(
            f"/api/v1/playlists/{p1_id}",
            headers=user_headers,
            json={"name": "Nhạc Tập Gym"},
        ).status_code
        == 409
    )
    assert (
        client.put(
            f"/api/v1/playlists/{p1_id}",
            headers=user_headers,
            json={"name": None},
        ).status_code
        == 422
    )

    updated = client.put(
        f"/api/v1/playlists/{p1_id}",
        headers=user_headers,
        json={"name": "Nhạc Chill Mới", "description": "Mô tả mới"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Nhạc Chill Mới"

    # Thêm bài hát (UC-10) & chặn trùng (BR-03)
    assert (
        client.post(
            f"/api/v1/playlists/{p1_id}/tracks",
            headers=user_headers,
            json={"track_id": 999999},
        ).status_code
        == 422
    )
    added = client.post(
        f"/api/v1/playlists/{p1_id}/tracks",
        headers=user_headers,
        json={"track_id": 1},
    )
    assert added.status_code == 201
    assert added.json()["track_id"] == 1
    assert (
        client.post(
            f"/api/v1/playlists/{p1_id}/tracks",
            headers=user_headers,
            json={"track_id": 1},
        ).status_code
        == 409
    )

    detail = client.get(f"/api/v1/playlists/{p1_id}", headers=user_headers)
    assert detail.status_code == 200
    assert len(detail.json()["tracks"]) == 1
    assert detail.json()["tracks"][0]["track"]["track_id"] == 1

    # Gỡ bài hát (UC-11)
    assert (
        client.delete(
            f"/api/v1/playlists/{p1_id}/tracks/1", headers=user_headers
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/playlists/{p1_id}/tracks/1", headers=user_headers
        ).status_code
        == 404
    )
    # Bài hát vẫn còn trong thư viện
    assert client.get("/api/v1/tracks/1").status_code == 200

    # Xóa playlist (UC-09)
    assert (
        client.post(
            f"/api/v1/playlists/{p1_id}/tracks",
            headers=user_headers,
            json={"track_id": 1},
        ).status_code
        == 201
    )
    assert client.delete(f"/api/v1/playlists/{p1_id}", headers=user_headers).status_code == 204
    assert client.get(f"/api/v1/playlists/{p1_id}", headers=user_headers).status_code == 404
    assert client.get("/api/v1/tracks/1").status_code == 200


def test_playlist_ownership_and_admin_moderation_uc17_br02(
    client: TestClient,
    user_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/playlists",
        headers=user_headers,
        json={"name": "Playlist Riêng Tư"},
    )
    assert created.status_code == 201
    pl_id = created.json()["playlist_id"]
    assert (
        client.post(
            f"/api/v1/playlists/{pl_id}/tracks",
            headers=user_headers,
            json={"track_id": 1},
        ).status_code
        == 201
    )

    # Người dùng thường không thể truy cập danh sách kiểm duyệt
    assert client.get("/api/v1/playlists", headers=user_headers).status_code == 403

    # Người dùng khác bị chặn hoàn toàn (BR-02)
    other_headers = get_auth_headers(client, "luisg", "luisg@123")
    assert client.get(f"/api/v1/playlists/{pl_id}", headers=other_headers).status_code == 403
    assert (
        client.put(
            f"/api/v1/playlists/{pl_id}", headers=other_headers, json={"name": "Hack"}
        ).status_code
        == 403
    )
    assert client.delete(f"/api/v1/playlists/{pl_id}", headers=other_headers).status_code == 403
    assert (
        client.post(
            f"/api/v1/playlists/{pl_id}/tracks",
            headers=other_headers,
            json={"track_id": 2},
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/playlists/{pl_id}/tracks/1", headers=other_headers
        ).status_code
        == 403
    )

    # Admin xem được để kiểm duyệt (UC-17), nhưng KHÔNG được sửa nội dung (BR-02)
    admin_list = client.get("/api/v1/playlists?user_id=2", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(pl["playlist_id"] == pl_id for pl in admin_list.json()["items"])

    assert client.get(f"/api/v1/playlists/{pl_id}", headers=admin_headers).status_code == 200
    assert (
        client.put(
            f"/api/v1/playlists/{pl_id}",
            headers=admin_headers,
            json={"name": "Admin Sửa"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/playlists/{pl_id}/tracks",
            headers=admin_headers,
            json={"track_id": 2},
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/playlists/{pl_id}/tracks/1", headers=admin_headers
        ).status_code
        == 403
    )

    # Admin được quyền xóa kiểm duyệt (UC-17)
    assert client.delete(f"/api/v1/playlists/{pl_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/playlists/{pl_id}", headers=admin_headers).status_code == 404
