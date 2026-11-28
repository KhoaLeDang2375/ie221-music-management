"""[NGƯỜI B] Pydantic Schemas cho Lịch sử nghe nhạc (UC-13)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HistoryTrackSummary(BaseModel):
    """Thông tin tóm tắt bài hát đính kèm trong mỗi bản ghi lịch sử nghe (UC-13)."""

    model_config = ConfigDict(from_attributes=True)

    track_id: int
    name: str
    album_id: Optional[int] = None
    media_type_id: int
    genre_id: Optional[int] = None
    composer: Optional[str] = None
    duration_ms: int


class HistoryCreateRequest(BaseModel):
    """Dữ liệu đầu vào khi ghi nhận người dùng vừa nghe một bài hát (UC-13)."""

    track_id: int = Field(..., gt=0)


class HistoryItemResponse(BaseModel):
    """Thông tin một lượt nghe gần đây kèm chi tiết tóm tắt bài hát (UC-13)."""

    model_config = ConfigDict(from_attributes=True)

    history_id: int
    user_id: int
    track_id: int
    listened_at: datetime
    track: HistoryTrackSummary
