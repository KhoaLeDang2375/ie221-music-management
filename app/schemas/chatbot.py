"""[NGƯỜI A] Pydantic Schemas cho tạo Playlist bằng Chatbot Groq (UC-12)."""
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.playlist import PlaylistDetail


class ChatbotPlaylistRequest(BaseModel):
    """Yêu cầu tạo playlist tự động từ mô tả ngôn ngữ tự nhiên (UC-12)."""

    prompt: str = Field(..., min_length=3, max_length=500)
    limit: int = Field(10, ge=1, le=50)


class ChatbotCriteria(BaseModel):
    """Tiêu chí tìm bài hát được Groq AI trích xuất từ prompt."""

    playlist_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    genres: list[str] = []
    keywords: list[str] = []
    limit: int = Field(10, ge=1, le=50)


class ChatbotPlaylistResponse(BaseModel):
    """Phản hồi sau khi Chatbot tạo xong playlist (UC-12)."""

    playlist: PlaylistDetail
    criteria: ChatbotCriteria
    matched_count: int