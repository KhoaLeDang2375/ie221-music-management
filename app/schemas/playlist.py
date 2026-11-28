"""[NGƯỜI A] Pydantic Schemas cho Playlist và Kiểm duyệt (UC-06..UC-11, UC-17)."""
from h11 import Data
from datetime import datetime
from typing import Optional,Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, AfterValidator

# Nhóm em định nghĩa hàm kiểm tra name để tái sử dụng  
def _validate_name_not_blank(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Tên playlist không được chỉ chứa khoảng trắng")
    return cleaned
PlaylistName = Annotated[
    str,
    Field(min_length=1, max_length=100),
    AfterValidator(_validate_name_not_blank),
]
class PlaylistCreate(BaseModel):
    """ Định nghĩa dữ liệu tạo playlist mới theo yêu cầu (UC-06, BR-05)"""

    name: PlaylistName
    description: Optional[str] = None

class PlaylistUpdate(BaseModel):
    """ Dữ liệu cập nhật playlist (UC-08, BR-05)"""

    name: Optional[PlaylistName] = None
    description: Optional[str] = None

class PlaylistSummary(BaseModel):
    """
        Thông tin tóm tắt từ một playlist.
    """
    playlist_id : int
    name: str
    description: Optional[str] = None
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlaylistTrackItem(BaseModel):
    """Thông tin bài hát hiển thị bên trong chi tiết của playlist."""
    track_id: int
    name: str
    duration_ms: int
    composer: Optional[str] = None
    added_at: datetime

class PlaylistDetail(PlaylistSummary):
    """Định nghĩa cấu trúc lưu thông tin chi tiết playlist kèm bài hát"""

    tracks: list[PlaylistTrackItem] = []

class PlaylistTrackAdd(BaseModel):
    """Dữ liệu để thêm bài hát vào playlist"""
    track_id: int = Field(..., ge=1)

class PlaylistTrackResponse(BaseModel):
    """Cấu trúc dữ liệu trả về sau khi người dùng thêm bài hát"""
    playlist_id: int 
    track_id: int
    added_at: datetime
    
    model_config = ConfigDict(from_attributes=True)