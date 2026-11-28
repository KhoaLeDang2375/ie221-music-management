"""[NGƯỜI B] Kiểm thử cho nhóm API Danh mục âm nhạc (UC-04, UC-15)."""

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


def test_catalog_public_list_and_detail(client: TestClient) -> None:
    """Kiểm tra xem danh sách và chi tiết công khai cho Artist, Album, Genre, MediaType."""
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


def test_artist_admin_crud_and_br04(client: TestClient) -> None:
    """Kiểm tra CRUD Nghệ sĩ, phân quyền admin, chống trùng tên và chặn xóa BR-04."""
    admin_headers = _get_auth_headers(client, "admin", "admin@123")
    user_headers = _get_auth_headers(client, "testuser", "testuser@123")

    assert (
        client.post("/api/v1/artists", headers=user_headers, json={"name": "New Band"}).status_code
        == 403
    )
    assert (
        client.post("/api/v1/artists", headers=admin_headers, json={"name": "   "}).status_code
        == 422
    )

    created = client.post(
        "/api/v1/artists", headers=admin_headers, json={"name": "Ngọt Band Test"}
    )
    assert created.status_code == 201
    artist_id = created.json()["artist_id"]

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

    # BR-04: Nghệ sĩ đang có album tham chiếu -> 409
    assert client.delete("/api/v1/artists/1", headers=admin_headers).status_code == 409

    # Nghệ sĩ rỗng vừa tạo -> xóa thành công 204
    assert client.delete(f"/api/v1/artists/{artist_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/artists/{artist_id}").status_code == 404


def test_album_admin_crud_and_br04(client: TestClient) -> None:
    """Kiểm tra CRUD Album, kiểm tra artist_id 422, chống trùng 409 và chặn xóa BR-04."""
    admin_headers = _get_auth_headers(client, "admin", "admin@123")

    assert (
        client.post(
            "/api/v1/albums",
            headers=admin_headers,
            json={"title": "Bad Album", "artist_id": 999999},
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

    # BR-04: Album đang có bài hát tham chiếu -> 409
    assert client.delete("/api/v1/albums/1", headers=admin_headers).status_code == 409

    # Album rỗng vừa tạo -> xóa thành công 204
    assert client.delete(f"/api/v1/albums/{album_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/albums/{album_id}").status_code == 404


def test_genre_admin_crud_and_br04(client: TestClient) -> None:
    """Kiểm tra CRUD Thể loại, chống trùng tên 409 và chặn xóa BR-04."""
    admin_headers = _get_auth_headers(client, "admin", "admin@123")

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

    # BR-04: Thể loại đang có bài hát tham chiếu -> 409
    assert client.delete("/api/v1/genres/1", headers=admin_headers).status_code == 409

    assert client.delete(f"/api/v1/genres/{genre_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/genres/{genre_id}").status_code == 404
