"""[NGƯỜI A] Kiểm thử cho nhóm API Chatbot tạo Playlist AI (UC-12)."""

from collections.abc import Generator

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import engine
from app.deps import get_db
from app.main import app
from app.models.playlist import Playlist
from app.schemas.chatbot import ChatbotCriteria
from app.services import chatbot_service
from app.services.chatbot_service import GroqClient


@pytest.fixture()
def db_and_client() -> Generator[tuple[Session, TestClient], None, None]:
    """Tạo TestClient và Session tự rollback, đồng thời reset rate limit."""
    chatbot_service._USER_CALL_TIMESTAMPS.clear()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield session, test_client

    app.dependency_overrides.clear()
    chatbot_service._USER_CALL_TIMESTAMPS.clear()
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


def test_generate_ai_unauthorized(db_and_client: tuple[Session, TestClient]) -> None:
    _, client = db_and_client
    res = client.post(
        "/api/v1/playlists/generate-ai",
        json={"prompt": "10 bài Rock để chạy bộ", "limit": 10},
    )
    assert res.status_code == 401


def test_generate_ai_success_and_duplicate_name_resolved(
    db_and_client: tuple[Session, TestClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, client = db_and_client
    headers = _get_auth_headers(client, "testuser", "testuser@123")

    def fake_extract(self, prompt: str, valid_genres: list[str], max_tracks: int) -> ChatbotCriteria:
        return ChatbotCriteria(
            playlist_name="Rock Chạy Bộ AI",
            description="Nhạc Rock năng lượng cao",
            genres=["Rock"],
            keywords=[],
            limit=min(5, max_tracks),
        )

    monkeypatch.setattr(GroqClient, "extract_criteria", fake_extract)

    res1 = client.post(
        "/api/v1/playlists/generate-ai",
        headers=headers,
        json={"prompt": "5 bài Rock để chạy bộ", "limit": 5},
    )
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["playlist"]["name"] == "Rock Chạy Bộ AI"
    assert 1 <= data1["matched_count"] <= 5
    assert len(data1["playlist"]["tracks"]) == data1["matched_count"]

    # Gọi lại lần 2 cùng tên gợi ý -> tự động thêm hậu tố (2) theo BR-05
    res2 = client.post(
        "/api/v1/playlists/generate-ai",
        headers=headers,
        json={"prompt": "5 bài Rock để chạy bộ", "limit": 5},
    )
    assert res2.status_code == 201
    assert res2.json()["playlist"]["name"] == "Rock Chạy Bộ AI (2)"


def test_generate_ai_no_matching_tracks_returns_404_and_no_empty_playlist(
    db_and_client: tuple[Session, TestClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, client = db_and_client
    headers = _get_auth_headers(client, "testuser", "testuser@123")

    before_count = session.scalar(select(func.count()).select_from(Playlist)) or 0

    def fake_extract(self, prompt: str, valid_genres: list[str], max_tracks: int) -> ChatbotCriteria:
        return ChatbotCriteria(
            playlist_name="Playlist Không Tồn Tại",
            description="Test 404",
            genres=[],
            keywords=["xyz_khong_co_bai_nao_khop_999999"],
            limit=5,
        )

    monkeypatch.setattr(GroqClient, "extract_criteria", fake_extract)

    res = client.post(
        "/api/v1/playlists/generate-ai",
        headers=headers,
        json={"prompt": "nhạc không có trong DB", "limit": 5},
    )
    assert res.status_code == 404

    after_count = session.scalar(select(func.count()).select_from(Playlist)) or 0
    assert after_count == before_count


def test_generate_ai_rate_limit_exceeded_returns_429(
    db_and_client: tuple[Session, TestClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, client = db_and_client
    headers = _get_auth_headers(client, "testuser", "testuser@123")

    def fake_extract(self, prompt: str, valid_genres: list[str], max_tracks: int) -> ChatbotCriteria:
        return ChatbotCriteria(
            playlist_name="Rate Limit Rock",
            description="Test BR-11",
            genres=["Rock"],
            keywords=[],
            limit=2,
        )

    monkeypatch.setattr(GroqClient, "extract_criteria", fake_extract)

    for _ in range(5):
        res = client.post(
            "/api/v1/playlists/generate-ai",
            headers=headers,
            json={"prompt": "2 bài Rock", "limit": 2},
        )
        assert res.status_code == 201

    # Lần gọi thứ 6 trong 1 phút -> 429 (BR-11)
    res_6th = client.post(
        "/api/v1/playlists/generate-ai",
        headers=headers,
        json={"prompt": "2 bài Rock", "limit": 2},
    )
    assert res_6th.status_code == 429


def test_generate_ai_groq_error_returns_503(
    db_and_client: tuple[Session, TestClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, client = db_and_client
    headers = _get_auth_headers(client, "testuser", "testuser@123")

    def fake_error(self, prompt: str, valid_genres: list[str], max_tracks: int) -> ChatbotCriteria:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ Groq API hiện đang lỗi hoặc không phản hồi",
        )

    monkeypatch.setattr(GroqClient, "extract_criteria", fake_error)

    res = client.post(
        "/api/v1/playlists/generate-ai",
        headers=headers,
        json={"prompt": "5 bài Jazz", "limit": 5},
    )
    assert res.status_code == 503
