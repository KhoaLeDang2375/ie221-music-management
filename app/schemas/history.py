"""[NGƯỜI B] Pydantic Schemas cho Lịch sử nghe nhạc (UC-13)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.track import TrackSummary


class HistoryCreateRequest(BaseModel):
    """Payload ghi nhận lượt nghe bài hát của người dùng (UC-13)."""

    track_id: int = Field(..., gt=0)


class HistoryItemResponse(BaseModel):
    """Thông tin một lượt nghe gần đây kèm chi tiết tóm tắt bài hát (UC-13)."""

    model_config = ConfigDict(from_attributes=True)

    history_id: int
    user_id: int
    track_id: int
    listened_at: datetime
    track: TrackSummary
