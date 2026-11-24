"""[NGƯỜI A] Pydantic Schemas cho Playlist và Kiểm duyệt (UC-06..UC-11, UC-17)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.playlist import Playlist
from app.schemas.track import TrackSummary


class PlaylistBase(BaseModel):
    """Các trường cơ bản của một playlist cá nhân."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    """Payload tạo mới playlist cá nhân (UC-06)."""


class PlaylistUpdate(BaseModel):
    """Payload cập nhật tên hoặc mô tả playlist (UC-08)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None


class PlaylistAddTrackRequest(BaseModel):
    """Payload thêm một bài hát vào playlist (UC-10)."""

    track_id: int = Field(..., gt=0)


class PlaylistTrackItem(BaseModel):
    """Thông tin một bài hát trong playlist kèm thời điểm thêm."""

    model_config = ConfigDict(from_attributes=True)

    playlist_id: int
    track_id: int
    added_at: datetime
    track: TrackSummary


class PlaylistSummary(BaseModel):
    """Thông tin tóm tắt playlist dùng cho phản hồi danh sách."""

    model_config = ConfigDict(from_attributes=True)

    playlist_id: int
    name: str
    description: Optional[str] = None
    user_id: int
    created_at: datetime


class PlaylistDetail(PlaylistSummary):
    """Thông tin chi tiết playlist kèm danh sách bài hát bên trong (UC-07, UC-17)."""

    tracks: list[PlaylistTrackItem] = Field(default_factory=list)

    @classmethod
    def from_orm_playlist(cls, playlist: Playlist) -> "PlaylistDetail":
        """Chuyển đổi ORM Playlist (đã nạp track_links) thành PlaylistDetail."""
        ordered_links = sorted(
            playlist.track_links,
            key=lambda link: (link.added_at, link.track_id),
        )
        return cls(
            playlist_id=playlist.playlist_id,
            name=playlist.name,
            description=playlist.description,
            user_id=playlist.user_id,
            created_at=playlist.created_at,
            tracks=[PlaylistTrackItem.model_validate(link) for link in ordered_links],
        )
