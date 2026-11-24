"""[NGƯỜI A] Kiểm thử cho API tạo Playlist bằng Chatbot (UC-12)."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.playlists import get_groq_client
from app.schemas.chatbot import ChatbotCriteria
from app.services.chatbot_service import ChatbotService, GroqClient


@pytest.fixture(autouse=True)
def reset_chatbot_state() -> Generator[None, None, None]:
    """Đặt lại rate limiter và override GroqClient sau mỗi test case."""
    ChatbotService.reset_rate_limits()
    yield
    ChatbotService.reset_rate_limits()
    app.dependency_overrides.pop(get_groq_client, None)


class FakeGroqClient(GroqClient):
    """GroqClient giả lập trả về tiêu chí xác định cho kiểm thử offline."""

    def __init__(self, criteria: ChatbotCriteria) -> None:
        super().__init__(api_key="fake-key", model_name="fake-model")
        self._criteria = criteria

    def extract_criteria(
        self,
        prompt: str,
        valid_genres: list[str],
        max_tracks: int,
    ) -> ChatbotCriteria:
        return self._criteria


def test_chatbot_generate_playlist_success_and_auto_suffix_br05(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    app.dependency_overrides[get_groq_client] = lambda: FakeGroqClient(
        ChatbotCriteria(
            playlist_name="Rock Chạy Bộ",
            description="Năng lượng cao",
            genres=["Rock"],
            artists=[],
            keywords=[],
            limit=8,
        )
    )

    first = client.post(
        "/api/v1/playlists/generate-ai",
        headers=user_headers,
        json={"prompt": "8 bài Rock để chạy bộ", "limit": 8},
    )
    assert first.status_code == 201
    data1 = first.json()
    assert data1["playlist"]["name"] == "Rock Chạy Bộ"
    assert len(data1["playlist"]["tracks"]) == 8
    track_ids = [item["track"]["track_id"] for item in data1["playlist"]["tracks"]]
    assert len(set(track_ids)) == 8
    assert data1["criteria_used"]["genres"] == ["Rock"]

    # Gọi lần 2 trùng tên -> tự động gắn hậu tố (2) theo BR-05
    second = client.post(
        "/api/v1/playlists/generate-ai",
        headers=user_headers,
        json={"prompt": "Thêm playlist Rock chạy bộ nữa", "limit": 8},
    )
    assert second.status_code == 201
    assert second.json()["playlist"]["name"] == "Rock Chạy Bộ (2)"


def test_chatbot_no_matching_tracks_returns_404_and_no_empty_playlist(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    before_count = client.get("/api/v1/playlists/me", headers=user_headers).json()["total"]
    app.dependency_overrides[get_groq_client] = lambda: FakeGroqClient(
        ChatbotCriteria(
            playlist_name="Không Tồn Tại",
            genres=["Thể Loại Không Có Trong DB"],
            artists=[],
            keywords=[],
            limit=10,
        )
    )

    res = client.post(
        "/api/v1/playlists/generate-ai",
        headers=user_headers,
        json={"prompt": "Nhạc ngoài hành tinh", "limit": 10},
    )
    assert res.status_code == 404
    after_count = client.get("/api/v1/playlists/me", headers=user_headers).json()["total"]
    assert after_count == before_count


def test_chatbot_rate_limit_5_per_minute_br11(
    client: TestClient,
    user_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    app.dependency_overrides[get_groq_client] = lambda: FakeGroqClient(
        ChatbotCriteria(
            playlist_name="Rate Limit Test",
            genres=["Rock"],
            limit=3,
        )
    )

    for _ in range(5):
        res = client.post(
            "/api/v1/playlists/generate-ai",
            headers=user_headers,
            json={"prompt": "3 bài Rock", "limit": 3},
        )
        assert res.status_code == 201

    blocked = client.post(
        "/api/v1/playlists/generate-ai",
        headers=user_headers,
        json={"prompt": "3 bài Rock", "limit": 3},
    )
    assert blocked.status_code == 429

    # Tài khoản khác vẫn có hạn mức riêng
    other_ok = client.post(
        "/api/v1/playlists/generate-ai",
        headers=admin_headers,
        json={"prompt": "3 bài Rock", "limit": 3},
    )
    assert other_ok.status_code == 201


def test_chatbot_groq_unavailable_503_and_malformed_json_422(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    before_count = client.get("/api/v1/playlists/me", headers=user_headers).json()["total"]

    # 1. Thiếu GROQ_API_KEY -> 503
    app.dependency_overrides[get_groq_client] = lambda: GroqClient(api_key="")
    res_no_key = client.post(
        "/api/v1/playlists/generate-ai",
        headers=user_headers,
        json={"prompt": "5 bài Jazz", "limit": 5},
    )
    assert res_no_key.status_code == 503

    # 2. Lỗi mạng khi gọi Groq -> 503
    app.dependency_overrides[get_groq_client] = lambda: GroqClient(api_key="test-key")
    with patch("app.services.chatbot_service.httpx.Client") as mock_http_cls:
        mock_http_cls.return_value.__enter__.return_value.post.side_effect = (
            httpx.ConnectError("network error")
        )
        res_net_err = client.post(
            "/api/v1/playlists/generate-ai",
            headers=user_headers,
            json={"prompt": "5 bài Jazz", "limit": 5},
        )
    assert res_net_err.status_code == 503

    # 3. Groq trả JSON sai cấu trúc -> 422
    bad_response = MagicMock()
    bad_response.status_code = 200
    bad_response.json.return_value = {
        "choices": [{"message": {"content": "not-valid-json"}}]
    }
    with patch("app.services.chatbot_service.httpx.Client") as mock_http_cls:
        mock_http_cls.return_value.__enter__.return_value.post.return_value = bad_response
        res_bad_json = client.post(
            "/api/v1/playlists/generate-ai",
            headers=user_headers,
            json={"prompt": "5 bài Jazz", "limit": 5},
        )
    assert res_bad_json.status_code == 422

    # NFR-02: Không tạo playlist rỗng khi gặp lỗi
    after_count = client.get("/api/v1/playlists/me", headers=user_headers).json()["total"]
    assert after_count == before_count
