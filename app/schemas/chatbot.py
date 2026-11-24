"""[NGƯỜI A] Pydantic Schemas cho tạo Playlist bằng Chatbot Groq (UC-12)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.playlist import PlaylistDetail


class ChatbotPlaylistRequest(BaseModel):
    """Yêu cầu tạo playlist tự động từ mô tả ngôn ngữ tự nhiên (UC-12)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    prompt: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class ChatbotCriteria(BaseModel):
    """Tiêu chí tìm kiếm bài hát được trích xuất và chuẩn hóa từ Groq LLM (UC-12)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    playlist_name: str = Field(default="AI Playlist", min_length=1, max_length=100)
    description: Optional[str] = None
    genres: list[str] = Field(default_factory=list)
    artists: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)


class ChatbotPlaylistResponse(BaseModel):
    """Phản hồi gồm playlist vừa tạo và tiêu chí đã áp dụng (UC-12)."""

    playlist: PlaylistDetail
    criteria_used: ChatbotCriteria
