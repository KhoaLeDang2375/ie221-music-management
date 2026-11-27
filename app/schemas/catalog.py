"""[NGƯỜI B] Pydantic Schemas cho Nghệ sĩ, Album, Thể loại, Định dạng (UC-04, UC-15)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CatalogTrackSummary(BaseModel):
    """Thông tin tóm tắt bài hát dùng khi hiển thị chi tiết một album (UC-04)."""

    model_config = ConfigDict(from_attributes=True)

    track_id: int
    name: str
    album_id: Optional[int] = None
    media_type_id: int
    genre_id: Optional[int] = None
    composer: Optional[str] = None
    duration_ms: int


class ArtistBase(BaseModel):
    """Dữ liệu đầu vào dùng chung khi tạo và cập nhật nghệ sĩ."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)


class ArtistCreate(ArtistBase):
    """Dữ liệu đầu vào khi quản trị viên tạo nghệ sĩ mới (UC-15)."""


class ArtistUpdate(ArtistBase):
    """Dữ liệu đầu vào khi quản trị viên cập nhật tên nghệ sĩ (UC-15)."""


class ArtistResponse(BaseModel):
    """Thông tin cơ bản của một nghệ sĩ."""

    model_config = ConfigDict(from_attributes=True)

    artist_id: int
    name: str


class AlbumResponse(BaseModel):
    """Thông tin cơ bản của một album."""

    model_config = ConfigDict(from_attributes=True)

    album_id: int
    title: str
    artist_id: int


class ArtistDetailResponse(ArtistResponse):
    """Thông tin chi tiết nghệ sĩ kèm danh sách album của nghệ sĩ đó (UC-04)."""

    albums: list[AlbumResponse] = Field(default_factory=list)


class AlbumBase(BaseModel):
    """Dữ liệu đầu vào dùng chung khi tạo và cập nhật album."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=160)
    artist_id: int = Field(..., gt=0)


class AlbumCreate(AlbumBase):
    """Dữ liệu đầu vào khi quản trị viên tạo album mới (UC-15)."""


class AlbumUpdate(AlbumBase):
    """Dữ liệu đầu vào khi quản trị viên cập nhật album (UC-15)."""


class AlbumDetailResponse(AlbumResponse):
    """Thông tin chi tiết album kèm tên nghệ sĩ và danh sách bài hát trong album (UC-04)."""

    artist_name: Optional[str] = None
    tracks: list[CatalogTrackSummary] = Field(default_factory=list)


class GenreBase(BaseModel):
    """Dữ liệu đầu vào dùng chung khi tạo và cập nhật thể loại nhạc."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120)


class GenreCreate(GenreBase):
    """Dữ liệu đầu vào khi quản trị viên tạo thể loại mới (UC-15)."""


class GenreUpdate(GenreBase):
    """Dữ liệu đầu vào khi quản trị viên cập nhật tên thể loại (UC-15)."""


class GenreResponse(BaseModel):
    """Thông tin của một thể loại nhạc."""

    model_config = ConfigDict(from_attributes=True)

    genre_id: int
    name: str


class MediaTypeResponse(BaseModel):
    """Thông tin của một định dạng âm thanh."""

    model_config = ConfigDict(from_attributes=True)

    media_type_id: int
    name: str
