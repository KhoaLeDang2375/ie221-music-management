"""[NGƯỜI B] Pydantic Schemas cho Nghệ sĩ, Album, Thể loại, Định dạng (UC-04, UC-15)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.track import TrackSummary


class ArtistBase(BaseModel):
    """Dữ liệu tên nghệ sĩ."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)


class ArtistCreate(ArtistBase):
    """Payload tạo nghệ sĩ mới (UC-15)."""


class ArtistUpdate(ArtistBase):
    """Payload cập nhật tên nghệ sĩ (UC-15)."""


class ArtistResponse(BaseModel):
    """Phản hồi thông tin nghệ sĩ."""

    model_config = ConfigDict(from_attributes=True)

    artist_id: int
    name: str


class AlbumResponse(BaseModel):
    """Phản hồi thông tin album cơ bản."""

    model_config = ConfigDict(from_attributes=True)

    album_id: int
    title: str
    artist_id: int


class ArtistDetailResponse(ArtistResponse):
    """Chi tiết nghệ sĩ kèm danh sách album của nghệ sĩ đó (UC-04)."""

    albums: list[AlbumResponse] = Field(default_factory=list)


class AlbumBase(BaseModel):
    """Dữ liệu tiêu đề album và nghệ sĩ phát hành."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=160)
    artist_id: int = Field(..., gt=0)


class AlbumCreate(AlbumBase):
    """Payload tạo album mới (UC-15)."""


class AlbumUpdate(AlbumBase):
    """Payload cập nhật album (UC-15)."""


class AlbumDetailResponse(AlbumResponse):
    """Chi tiết album kèm tên nghệ sĩ và danh sách bài hát trong album (UC-04)."""

    artist_name: Optional[str] = None
    tracks: list[TrackSummary] = Field(default_factory=list)


class GenreBase(BaseModel):
    """Dữ liệu tên thể loại nhạc."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)


class GenreCreate(GenreBase):
    """Payload tạo thể loại mới (UC-15)."""


class GenreUpdate(GenreBase):
    """Payload cập nhật thể loại (UC-15)."""


class GenreResponse(BaseModel):
    """Phản hồi thông tin thể loại nhạc."""

    model_config = ConfigDict(from_attributes=True)

    genre_id: int
    name: str


class MediaTypeResponse(BaseModel):
    """Phản hồi thông tin định dạng âm thanh."""

    model_config = ConfigDict(from_attributes=True)

    media_type_id: int
    name: str
