"""[NGƯỜI B] Router /api/v1/artists, /albums, /genres, /media-types (UC-04, UC-15)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models.catalog import Album, Artist, Genre, MediaType
from app.models.user import AppUser
from app.schemas.catalog import (
    AlbumCreate,
    AlbumDetailResponse,
    AlbumResponse,
    AlbumUpdate,
    ArtistCreate,
    ArtistDetailResponse,
    ArtistResponse,
    ArtistUpdate,
    GenreCreate,
    GenreResponse,
    GenreUpdate,
    MediaTypeResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


# -----------------------------------------------------------------------------
# Artists
# -----------------------------------------------------------------------------


@router.get(
    "/artists",
    response_model=PaginatedResponse[ArtistResponse],
    summary="Xem danh sách nghệ sĩ có phân trang (UC-04)",
)
def list_artists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Tìm theo tên nghệ sĩ"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ArtistResponse]:
    """Công khai cho mọi người dùng: xem danh sách nghệ sĩ."""
    return CatalogService(db).list_artists(page=page, page_size=page_size, q=q)


@router.get(
    "/artists/{artist_id}",
    response_model=ArtistDetailResponse,
    summary="Xem chi tiết nghệ sĩ kèm danh sách album (UC-04)",
)
def get_artist_detail(
    artist_id: int,
    db: Session = Depends(get_db),
) -> ArtistDetailResponse:
    """Công khai cho mọi người dùng: xem chi tiết nghệ sĩ theo ID."""
    return CatalogService(db).get_artist_with_albums(artist_id)


@router.post(
    "/artists",
    status_code=status.HTTP_201_CREATED,
    response_model=ArtistResponse,
    summary="Quản trị viên thêm nghệ sĩ mới (UC-15)",
)
def create_artist(
    data: ArtistCreate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Artist:
    """Quản trị viên thêm nghệ sĩ mới."""
    return CatalogService(db).create_artist(data)


@router.put(
    "/artists/{artist_id}",
    response_model=ArtistResponse,
    summary="Quản trị viên cập nhật nghệ sĩ (UC-15)",
)
def update_artist(
    artist_id: int,
    data: ArtistUpdate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Artist:
    """Quản trị viên cập nhật tên nghệ sĩ."""
    return CatalogService(db).update_artist(artist_id, data)


@router.delete(
    "/artists/{artist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quản trị viên xóa nghệ sĩ (UC-15, BR-04)",
)
def delete_artist(
    artist_id: int,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Quản trị viên xóa nghệ sĩ nếu chưa có album tham chiếu."""
    CatalogService(db).delete_artist(artist_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Albums
# -----------------------------------------------------------------------------


@router.get(
    "/albums",
    response_model=PaginatedResponse[AlbumResponse],
    summary="Xem danh sách album có phân trang (UC-04)",
)
def list_albums(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    artist_id: Optional[int] = Query(None, ge=1),
    q: Optional[str] = Query(None, description="Tìm theo tiêu đề album"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AlbumResponse]:
    """Công khai cho mọi người dùng: xem danh sách album."""
    return CatalogService(db).list_albums(
        page=page, page_size=page_size, artist_id=artist_id, q=q
    )


@router.get(
    "/albums/{album_id}",
    response_model=AlbumDetailResponse,
    summary="Xem chi tiết album kèm danh sách bài hát (UC-04)",
)
def get_album_detail(
    album_id: int,
    db: Session = Depends(get_db),
) -> AlbumDetailResponse:
    """Công khai cho mọi người dùng: xem chi tiết album theo ID."""
    return CatalogService(db).get_album_with_tracks(album_id)


@router.post(
    "/albums",
    status_code=status.HTTP_201_CREATED,
    response_model=AlbumResponse,
    summary="Quản trị viên thêm album mới (UC-15)",
)
def create_album(
    data: AlbumCreate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Album:
    """Quản trị viên thêm album mới."""
    return CatalogService(db).create_album(data)


@router.put(
    "/albums/{album_id}",
    response_model=AlbumResponse,
    summary="Quản trị viên cập nhật album (UC-15)",
)
def update_album(
    album_id: int,
    data: AlbumUpdate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Album:
    """Quản trị viên cập nhật thông tin album."""
    return CatalogService(db).update_album(album_id, data)


@router.delete(
    "/albums/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quản trị viên xóa album (UC-15, BR-04)",
)
def delete_album(
    album_id: int,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Quản trị viên xóa album nếu chưa có bài hát tham chiếu."""
    CatalogService(db).delete_album(album_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Genres
# -----------------------------------------------------------------------------


@router.get(
    "/genres",
    response_model=PaginatedResponse[GenreResponse],
    summary="Xem danh sách thể loại nhạc có phân trang (UC-04)",
)
def list_genres(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Tìm theo tên thể loại"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GenreResponse]:
    """Công khai cho mọi người dùng: xem danh sách thể loại."""
    return CatalogService(db).list_genres(page=page, page_size=page_size, q=q)


@router.get(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    summary="Xem chi tiết thể loại nhạc (UC-04)",
)
def get_genre_detail(
    genre_id: int,
    db: Session = Depends(get_db),
) -> Genre:
    """Công khai cho mọi người dùng: xem chi tiết thể loại theo ID."""
    return CatalogService(db).get_genre_by_id(genre_id)


@router.post(
    "/genres",
    status_code=status.HTTP_201_CREATED,
    response_model=GenreResponse,
    summary="Quản trị viên thêm thể loại mới (UC-15)",
)
def create_genre(
    data: GenreCreate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Genre:
    """Quản trị viên thêm thể loại nhạc mới."""
    return CatalogService(db).create_genre(data)


@router.put(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    summary="Quản trị viên cập nhật thể loại (UC-15)",
)
def update_genre(
    genre_id: int,
    data: GenreUpdate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Genre:
    """Quản trị viên cập nhật tên thể loại."""
    return CatalogService(db).update_genre(genre_id, data)


@router.delete(
    "/genres/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quản trị viên xóa thể loại (UC-15, BR-04)",
)
def delete_genre(
    genre_id: int,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Quản trị viên xóa thể loại nếu chưa có bài hát tham chiếu."""
    CatalogService(db).delete_genre(genre_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Media Types
# -----------------------------------------------------------------------------


@router.get(
    "/media-types",
    response_model=PaginatedResponse[MediaTypeResponse],
    summary="Xem danh sách định dạng âm thanh có phân trang (UC-04)",
)
def list_media_types(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[MediaTypeResponse]:
    """Công khai cho mọi người dùng: xem danh sách định dạng âm thanh."""
    return CatalogService(db).list_media_types(page=page, page_size=page_size)


@router.get(
    "/media-types/{media_type_id}",
    response_model=MediaTypeResponse,
    summary="Xem chi tiết định dạng âm thanh (UC-04)",
)
def get_media_type_detail(
    media_type_id: int,
    db: Session = Depends(get_db),
) -> MediaType:
    """Công khai cho mọi người dùng: xem chi tiết định dạng theo ID."""
    return CatalogService(db).get_media_type_by_id(media_type_id)
