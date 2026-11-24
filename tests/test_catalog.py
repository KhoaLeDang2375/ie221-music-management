"""[NGƯỜI B] Kiểm thử cho nhóm API Danh mục âm nhạc (UC-04, UC-15)."""

from fastapi.testclient import TestClient


def test_catalog_public_list_and_detail(client: TestClient) -> None:
    res_artists = client.get("/api/v1/artists?page=1&page_size=10")
    assert res_artists.status_code == 200
    assert res_artists.json()["total"] >= 275

    res_artist_detail = client.get("/api/v1/artists/1")
    assert res_artist_detail.status_code == 200
    assert len(res_artist_detail.json()["albums"]) >= 1
    assert client.get("/api/v1/artists/999999").status_code == 404

    res_albums = client.get("/api/v1/albums?artist_id=1")
    assert res_albums.status_code == 200
    assert all(al["artist_id"] == 1 for al in res_albums.json()["items"])

    res_album_detail = client.get("/api/v1/albums/1")
    assert res_album_detail.status_code == 200
    assert res_album_detail.json()["artist_name"] is not None
    assert len(res_album_detail.json()["tracks"]) >= 1
    assert client.get("/api/v1/albums/999999").status_code == 404

    res_genres = client.get("/api/v1/genres")
    assert res_genres.status_code == 200
    assert res_genres.json()["total"] >= 25
    assert client.get("/api/v1/genres/1").status_code == 200
    assert client.get("/api/v1/genres/999999").status_code == 404

    res_media = client.get("/api/v1/media-types")
    assert res_media.status_code == 200
    assert res_media.json()["total"] >= 5
    assert client.get("/api/v1/media-types/1").status_code == 200
    assert client.get("/api/v1/media-types/999999").status_code == 404


def test_artist_admin_crud_and_br04(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    assert (
        client.post("/api/v1/artists", headers=user_headers, json={"name": "New Band"}).status_code
        == 403
    )
    assert (
        client.post("/api/v1/artists", headers=admin_headers, json={"name": "   "}).status_code
        == 422
    )

    created = client.post("/api/v1/artists", headers=admin_headers, json={"name": "Ngọt Band Test"})
    assert created.status_code == 201
    artist_id = created.json()["artist_id"]

    # Trùng tên (không phân biệt hoa/thường) -> 409
    assert (
        client.post(
            "/api/v1/artists", headers=admin_headers, json={"name": "ngọt band test"}
        ).status_code
        == 409
    )

    updated = client.put(
        f"/api/v1/artists/{artist_id}",
        headers=admin_headers,
        json={"name": "Ngọt Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Ngọt Updated"
    assert (
        client.put(
            f"/api/v1/artists/{artist_id}", headers=admin_headers, json={"name": "AC/DC"}
        ).status_code
        == 409
    )
    assert (
        client.put(
            "/api/v1/artists/999999", headers=admin_headers, json={"name": "Missing"}
        ).status_code
        == 404
    )

    # BR-04: Nghệ sĩ đang có album -> 409
    assert client.delete("/api/v1/artists/1", headers=admin_headers).status_code == 409

    # Nghệ sĩ rỗng vừa tạo -> xóa thành công 204
    assert client.delete(f"/api/v1/artists/{artist_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/artists/{artist_id}").status_code == 404


def test_album_admin_crud_and_br04(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    assert (
        client.post(
            "/api/v1/albums", headers=admin_headers, json={"title": "Bad Album", "artist_id": 999999}
        ).status_code
        == 422
    )

    created = client.post(
        "/api/v1/albums",
        headers=admin_headers,
        json={"title": "Album Kiểm Thử", "artist_id": 1},
    )
    assert created.status_code == 201
    album_id = created.json()["album_id"]

    assert (
        client.post(
            "/api/v1/albums",
            headers=admin_headers,
            json={"title": "album kiểm thử", "artist_id": 1},
        ).status_code
        == 409
    )

    updated = client.put(
        f"/api/v1/albums/{album_id}",
        headers=admin_headers,
        json={"title": "Album Mới", "artist_id": 1},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Album Mới"

    # BR-04: Album đang có bài hát -> 409
    assert client.delete("/api/v1/albums/1", headers=admin_headers).status_code == 409

    # Album rỗng vừa tạo -> xóa thành công 204
    assert client.delete(f"/api/v1/albums/{album_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/albums/{album_id}").status_code == 404


def test_genre_admin_crud_and_br04(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    created = client.post(
        "/api/v1/genres",
        headers=admin_headers,
        json={"name": "Lo-fi Việt Test"},
    )
    assert created.status_code == 201
    genre_id = created.json()["genre_id"]

    assert (
        client.post(
            "/api/v1/genres", headers=admin_headers, json={"name": "lo-fi việt test"}
        ).status_code
        == 409
    )

    updated = client.put(
        f"/api/v1/genres/{genre_id}",
        headers=admin_headers,
        json={"name": "Chillout Việt"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Chillout Việt"
    assert (
        client.put(
            f"/api/v1/genres/{genre_id}", headers=admin_headers, json={"name": "Rock"}
        ).status_code
        == 409
    )

    # BR-04: Thể loại đang có bài hát -> 409
    assert client.delete("/api/v1/genres/1", headers=admin_headers).status_code == 409

    assert client.delete(f"/api/v1/genres/{genre_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/genres/{genre_id}").status_code == 404
