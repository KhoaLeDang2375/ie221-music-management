"""[NGƯỜI B] Pydantic Schemas cho Bài hát (UC-03, UC-14)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.catalog import Track


class TrackBase(BaseModel):
    """Các trường dữ liệu đầu vào dùng chung khi tạo và cập nhật bài hát."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=200)
    album_id: Optional[int] = Field(default=None, gt=0)
    media_type_id: int = Field(..., gt=0)
    genre_id: Optional[int] = Field(default=None, gt=0)
    composer: Optional[str] = Field(default=None, max_length=220)
    duration_ms: int = Field(..., gt=0)

    @field_validator("composer")
    @classmethod
    def _empty_composer_to_none(cls, value: Optional[str]) -> Optional[str]:
        """Chuyển chuỗi composer rỗng sau khi cắt khoảng trắng thành None.

        Args:
            value: Chuỗi tên nhạc sĩ sau khi bỏ khoảng trắng đầu/cuối, hoặc None.

        Returns:
            None nếu chuỗi rỗng, ngược lại trả về chuỗi đã chuẩn hóa.
        """
        if value == "":
            return None
        return value


class TrackCreate(TrackBase):
    """Dữ liệu đầu vào khi quản trị viên thêm bài hát mới (UC-14)."""


class TrackUpdate(TrackBase):
    """Dữ liệu đầu vào khi quản trị viên cập nhật bài hát (UC-14)."""


class TrackSummary(BaseModel):
    """Thông tin tóm tắt bài hát dùng trong danh sách phân trang (UC-03)."""

    model_config = ConfigDict(from_attributes=True)

    track_id: int
    name: str
    album_id: Optional[int] = None
    media_type_id: int
    genre_id: Optional[int] = None
    composer: Optional[str] = None
    duration_ms: int


class TrackDetail(TrackSummary):
    """Thông tin chi tiết bài hát kèm tên album, nghệ sĩ, thể loại, định dạng (UC-03)."""

    album_title: Optional[str] = None
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    genre_name: Optional[str] = None
    media_type_name: str

    @classmethod
    def from_orm_track(cls, track: Track) -> "TrackDetail":
        """Chuyển đổi đối tượng ORM Track (đã nạp quan hệ) sang TrackDetail.

        Args:
            track: Đối tượng SQLAlchemy Track đã nạp sẵn album, artist, genre, media_type.

        Returns:
            Đối tượng TrackDetail đầy đủ thông tin bài hát và tên các danh mục liên kết.
        """
        album = track.album
        artist = album.artist if album is not None else None
        return cls(
            track_id=track.track_id,
            name=track.name,
            album_id=track.album_id,
            media_type_id=track.media_type_id,
            genre_id=track.genre_id,
            composer=track.composer,
            duration_ms=track.duration_ms,
            album_title=album.title if album is not None else None,
            artist_id=artist.artist_id if artist is not None else None,
            artist_name=artist.name if artist is not None else None,
            genre_name=track.genre.name if track.genre is not None else None,
            media_type_name=track.media_type.name,
        )
