"""[NGƯỜI A] Lớp ChatbotService và GroqClient xử lý nghiệp vụ UC-12."""

import json
import time
from collections import defaultdict, deque
from typing import Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.catalog import Album, Artist, Genre, Track
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import AppUser
from app.schemas.chatbot import (
    ChatbotCriteria,
    ChatbotPlaylistRequest,
    ChatbotPlaylistResponse,
)
from app.services.base import BaseService
from app.services.playlist_service import PlaylistService

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
RATE_LIMIT_MAX_CALLS = 5
RATE_LIMIT_WINDOW_SECONDS = 60.0

# Lưu mốc thời gian các lần gọi theo user_id (in-memory)
_USER_CALL_TIMESTAMPS: dict[int, deque[float]] = defaultdict(deque)


class GroqClient:
    """Client gọi Groq Cloud API để trích xuất tiêu chí tìm nhạc dạng JSON."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self.model_name = model_name or settings.GROQ_MODEL

    def extract_criteria(
        self,
        prompt: str,
        valid_genres: list[str],
        max_tracks: int,
    ) -> ChatbotCriteria:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ Chatbot AI chưa được cấu hình GROQ_API_KEY",
            )

        system_prompt = (
            "Bạn là trợ lý âm nhạc. Hãy phân tích yêu cầu người dùng và trả về DUY NHẤT "
            "một JSON object với các trường: "
            '"playlist_name" (chuỗi tiếng Việt ngắn gọn <= 80 ký tự), '
            '"description" (mô tả ngắn), '
            '"genres" (mảng tên thể loại CHỈ chọn từ danh sách sau: '
            f"{json.dumps(valid_genres, ensure_ascii=False)}), "
            '"keywords" (mảng từ khóa tiếng Anh/Việt để tìm theo tên bài hát hoặc nghệ sĩ), '
            f'"limit" (số nguyên từ 1 đến {max_tracks}).'
        )

        payload = {
            "model": self.model_name,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = httpx.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed["limit"] = min(max(int(parsed.get("limit", max_tracks)), 1), max_tracks)
            return ChatbotCriteria.model_validate(parsed)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ Groq API hiện đang lỗi hoặc không phản hồi",
            ) from exc


class ChatbotService(BaseService):
    """Xử lý nghiệp vụ tạo playlist tự động bằng AI (UC-12, BR-05, BR-10, BR-11)."""

    def __init__(
        self,
        db: Session,
        groq_client: Optional[GroqClient] = None,
    ) -> None:
        super().__init__(db)
        self.groq_client = groq_client or GroqClient()
        self.playlist_service = PlaylistService(db)

    def _check_rate_limit(self, user_id: int) -> None:
        """Giới hạn tối đa 5 lần gọi/phút/user (BR-11)."""
        now = time.monotonic()
        calls = _USER_CALL_TIMESTAMPS[user_id]
        while calls and now - calls[0] > RATE_LIMIT_WINDOW_SECONDS:
            calls.popleft()

        if len(calls) >= RATE_LIMIT_MAX_CALLS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đã vượt quá giới hạn 5 lần gọi chatbot mỗi phút",
            )
        calls.append(now)

    def _resolve_unique_playlist_name(self, user_id: int, base_name: str) -> str:
        """Tự động thêm hậu tố (2), (3)... nếu tên playlist bị trùng (BR-05)."""
        cleaned = base_name.strip()[:100] or "AI Playlist"
        candidate = cleaned
        suffix = 2
        while (
            self.db.scalar(
                select(Playlist).where(
                    Playlist.user_id == user_id,
                    Playlist.name == candidate,
                )
            )
            is not None
        ):
            tag = f" ({suffix})"
            candidate = f"{cleaned[: 100 - len(tag)]}{tag}"
            suffix += 1
        return candidate

    def _find_matching_tracks(
        self,
        criteria: ChatbotCriteria,
        limit: int,
    ) -> list[Track]:
        """Truy vấn các bài hát CÓ THẬT trong thư viện theo tiêu chí AI (BR-10)."""
        conditions = []
        if criteria.genres:
            conditions.append(Genre.name.in_(criteria.genres))
        for kw in criteria.keywords:
            kw_clean = kw.strip()
            if kw_clean:
                pattern = f"%{kw_clean}%"
                conditions.append(Track.name.ilike(pattern))
                conditions.append(Artist.name.ilike(pattern))

        if not conditions:
            return []

        stmt = (
            select(Track)
            .outerjoin(Genre, Track.genre_id == Genre.genre_id)
            .outerjoin(Album, Track.album_id == Album.album_id)
            .outerjoin(Artist, Album.artist_id == Artist.artist_id)
            .where(or_(*conditions))
            .distinct()
            .limit(min(limit, 50))
        )
        return list(self.db.scalars(stmt).all())

    def generate_playlist_from_prompt(
        self,
        user: AppUser,
        req: ChatbotPlaylistRequest,
    ) -> ChatbotPlaylistResponse:
        self._check_rate_limit(user.user_id)

        valid_genres = list(self.db.scalars(select(Genre.name)).all())
        criteria = self.groq_client.extract_criteria(
            prompt=req.prompt,
            valid_genres=valid_genres,
            max_tracks=req.limit,
        )

        target_limit = min(req.limit, criteria.limit, 50)
        tracks = self._find_matching_tracks(criteria, target_limit)
        if not tracks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy bài hát nào phù hợp với yêu cầu của bạn",
            )

        unique_name = self._resolve_unique_playlist_name(
            user.user_id, criteria.playlist_name
        )

        try:
            playlist = Playlist(
                name=unique_name,
                description=criteria.description or f"Tạo từ AI: {req.prompt}",
                user_id=user.user_id,
            )
            self.db.add(playlist)
            self.db.flush()  # Lấy playlist_id trước khi thêm các dòng PlaylistTrack

            for track in tracks:
                self.db.add(
                    PlaylistTrack(
                        playlist_id=playlist.playlist_id,
                        track_id=track.track_id,
                    )
                )
            self.db.commit()
            self.db.refresh(playlist)
        except Exception:
            self.db.rollback()
            raise

        detail = self.playlist_service.get_playlist_detail(user, playlist.playlist_id)
        return ChatbotPlaylistResponse(
            playlist=detail,
            criteria=criteria,
            matched_count=len(tracks),
        )