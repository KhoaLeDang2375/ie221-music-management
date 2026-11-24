"""[NGƯỜI B] Kiểm thử cho nhóm API Bài hát (UC-03, UC-14)."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.playlist import PlaylistTrack


def test_list_tracks_public_pagination_and_bounds(client: TestClient) -> None:
    res = client.get("/api/v1/tracks?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 3500
    assert len(data["items"]) == 10

    assert client.get("/api/v1/tracks?page=0").status_code == 422
    assert client.get("/api/v1/tracks?page_size=101").status_code == 422


def test_search_tracks_filters_sort_and_empty_result(client: TestClient) -> None:
    res = client.get(
        "/api/v1/tracks",
        params={"artist_id": 1, "album_id": 1, "q": "rock", "sort_by": "duration_ms", "order": "desc"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1
    assert any("rock" in item["name"].lower() for item in items)

    res_sort = client.get(
        "/api/v1/tracks",
        params={"genre_id": 1, "sort_by": "duration_ms", "order": "desc", "page_size": 5},
    )
    assert res_sort.status_code == 200
    durations = [item["duration_ms"] for item in res_sort.json()["items"]]
    assert durations == sorted(durations, reverse=True)

    res_empty = client.get("/api/v1/tracks", params={"q": "zz_khong_co_bai_nay_999"})
    assert res_empty.status_code == 200
    assert res_empty.json()["items"] == []
    assert res_empty.json()["total"] == 0


def test_search_tracks_vietnamese_accent_insensitive(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    created = client.post(
        "/api/v1/tracks",
        headers=admin_headers,
        json={
            "name": "Nơi Này Có Anh",
            "album_id": 1,
            "media_type_id": 1,
            "genre_id": 1,
            "composer": "Sơn Tùng M-TP",
            "duration_ms": 260000,
        },
    )
    assert created.status_code == 201

    res_no_accent = client.get("/api/v1/tracks", params={"q": "noi nay co anh"})
    assert res_no_accent.status_code == 200
    assert any(t["name"] == "Nơi Này Có Anh" for t in res_no_accent.json()["items"])

    res_with_accent = client.get("/api/v1/tracks", params={"q": "Nơi Này"})
    assert res_with_accent.status_code == 200
    assert any(t["name"] == "Nơi Này Có Anh" for t in res_with_accent.json()["items"])


def test_get_track_detail_success_and_not_found(client: TestClient) -> None:
    res = client.get("/api/v1/tracks/1")
    assert res.status_code == 200
    data = res.json()
    assert data["track_id"] == 1
    assert data["album_title"] is not None
    assert data["artist_name"] is not None
    assert data["media_type_name"] is not None

    assert client.get("/api/v1/tracks/999999").status_code == 404


def test_track_admin_crud_validation_and_cascade_delete(
    client: TestClient,
    db_session: Session,
    admin_headers: dict[str, str],
    user_headers: dict[str, str],
) -> None:
    payload = {
        "name": "  Bài Hát Kiểm Thử  ",
        "album_id": 1,
        "media_type_id": 1,
        "genre_id": 1,
        "composer": "Nhạc Sĩ Test",
        "duration_ms": 215000,
    }
    assert client.post("/api/v1/tracks", json=payload).status_code == 401
    assert client.post("/api/v1/tracks", headers=user_headers, json=payload).status_code == 403

    bad_duration = {**payload, "duration_ms": 0}
    assert client.post("/api/v1/tracks", headers=admin_headers, json=bad_duration).status_code == 422

    bad_album = {**payload, "album_id": 999999}
    assert client.post("/api/v1/tracks", headers=admin_headers, json=bad_album).status_code == 422

    bad_media = {**payload, "media_type_id": 999999}
    assert client.post("/api/v1/tracks", headers=admin_headers, json=bad_media).status_code == 422

    bad_genre = {**payload, "genre_id": 999999}
    assert client.post("/api/v1/tracks", headers=admin_headers, json=bad_genre).status_code == 422

    created = client.post("/api/v1/tracks", headers=admin_headers, json=payload)
    assert created.status_code == 201
    track_id = created.json()["track_id"]
    assert created.json()["name"] == "Bài Hát Kiểm Thử"

    updated = client.put(
        f"/api/v1/tracks/{track_id}",
        headers=admin_headers,
        json={**payload, "name": "Bài Hát Đã Sửa", "duration_ms": 180000},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Bài Hát Đã Sửa"
    assert updated.json()["duration_ms"] == 180000

    assert (
        client.put("/api/v1/tracks/999999", headers=admin_headers, json=payload).status_code == 404
    )

    # Gắn bài hát vào playlist #1 để kiểm tra BR-04 tự gỡ khi xóa bài hát
    db_session.add(PlaylistTrack(playlist_id=1, track_id=track_id))
    db_session.flush()

    deleted = client.delete(f"/api/v1/tracks/{track_id}", headers=admin_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/tracks/{track_id}").status_code == 404
    remaining_link = db_session.scalar(
        select(PlaylistTrack).where(PlaylistTrack.track_id == track_id)
    )
    assert remaining_link is None
    assert client.delete(f"/api/v1/tracks/{track_id}", headers=admin_headers).status_code == 404
