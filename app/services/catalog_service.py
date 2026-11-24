"""[NGƯỜI B] Lớp CatalogService xử lý nghiệp vụ Nghệ sĩ, Album, Thể loại, Định dạng (UC-04, UC-15)."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.models.catalog import Album, Artist, Genre, MediaType, Track
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
from app.schemas.track import TrackSummary
from app.services.base import BaseService
from app.services.track_service import build_vi_contains_filter


class CatalogService(BaseService):
    """Xử lý xem và quản trị danh mục Nghệ sĩ, Album, Thể loại, Định dạng âm thanh."""

    # -------------------------------------------------------------------------
    # Artists
    # -------------------------------------------------------------------------

    def list_artists(
        self,
        page: int = 1,
        page_size: int = 20,
        q: Optional[str] = None,
    ) -> PaginatedResponse[ArtistResponse]:
        """Lấy danh sách nghệ sĩ có phân trang và tìm theo tên (UC-04)."""
        query = select(Artist)
        count_query = select(func.count()).select_from(Artist)
        if q is not None and q.strip():
            cond = build_vi_contains_filter(Artist.name, q)
            query = query.where(cond)
            count_query = count_query.where(cond)

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        artists = list(
            self.db.scalars(
                query.order_by(Artist.name.asc(), Artist.artist_id.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return PaginatedResponse[ArtistResponse](
            items=[ArtistResponse.model_validate(a) for a in artists],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_artist_with_albums(self, artist_id: int) -> ArtistDetailResponse:
        """Xem chi tiết nghệ sĩ kèm danh sách album (UC-04)."""
        artist = self.db.scalar(
            select(Artist)
            .options(selectinload(Artist.albums))
            .where(Artist.artist_id == artist_id)
        )
        if artist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nghệ sĩ không tồn tại",
            )
        albums = sorted(artist.albums, key=lambda al: (al.title.lower(), al.album_id))
        return ArtistDetailResponse(
            artist_id=artist.artist_id,
            name=artist.name,
            albums=[AlbumResponse.model_validate(al) for al in albums],
        )

    def create_artist(self, data: ArtistCreate) -> Artist:
        """Quản trị viên tạo nghệ sĩ mới, từ chối nếu trùng tên (UC-15)."""
        duplicate = self.db.scalar(
            select(Artist).where(func.lower(Artist.name) == data.name.lower())
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên nghệ sĩ đã tồn tại",
            )
        return self._commit_and_refresh(Artist(name=data.name))

    def update_artist(self, artist_id: int, data: ArtistUpdate) -> Artist:
        """Quản trị viên cập nhật tên nghệ sĩ (UC-15)."""
        artist = self.db.get(Artist, artist_id)
        if artist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nghệ sĩ không tồn tại",
            )
        duplicate = self.db.scalar(
            select(Artist).where(
                func.lower(Artist.name) == data.name.lower(),
                Artist.artist_id != artist_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên nghệ sĩ đã tồn tại",
            )
        artist.name = data.name
        return self._commit_and_refresh(artist)

    def delete_artist(self, artist_id: int) -> None:
        """Xóa nghệ sĩ; chặn nếu đang có album tham chiếu theo BR-04 (UC-15)."""
        artist = self.db.get(Artist, artist_id)
        if artist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nghệ sĩ không tồn tại",
            )
        has_album = self.db.scalar(
            select(Album.album_id).where(Album.artist_id == artist_id).limit(1)
        )
        if has_album is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa nghệ sĩ đang có album tham chiếu",
            )
        self._delete_and_commit(artist)

    # -------------------------------------------------------------------------
    # Albums
    # -------------------------------------------------------------------------

    def list_albums(
        self,
        page: int = 1,
        page_size: int = 20,
        artist_id: Optional[int] = None,
        q: Optional[str] = None,
    ) -> PaginatedResponse[AlbumResponse]:
        """Lấy danh sách album có phân trang, hỗ trợ lọc theo nghệ sĩ (UC-04)."""
        query = select(Album)
        count_query = select(func.count()).select_from(Album)
        if artist_id is not None:
            query = query.where(Album.artist_id == artist_id)
            count_query = count_query.where(Album.artist_id == artist_id)
        if q is not None and q.strip():
            cond = build_vi_contains_filter(Album.title, q)
            query = query.where(cond)
            count_query = count_query.where(cond)

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        albums = list(
            self.db.scalars(
                query.order_by(Album.title.asc(), Album.album_id.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return PaginatedResponse[AlbumResponse](
            items=[AlbumResponse.model_validate(al) for al in albums],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_album_with_tracks(self, album_id: int) -> AlbumDetailResponse:
        """Xem chi tiết album kèm tên nghệ sĩ và danh sách bài hát (UC-04)."""
        album = self.db.scalar(
            select(Album)
            .options(joinedload(Album.artist), selectinload(Album.tracks))
            .where(Album.album_id == album_id)
        )
        if album is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album không tồn tại",
            )
        tracks = sorted(album.tracks, key=lambda tr: tr.track_id)
        return AlbumDetailResponse(
            album_id=album.album_id,
            title=album.title,
            artist_id=album.artist_id,
            artist_name=album.artist.name if album.artist is not None else None,
            tracks=[TrackSummary.model_validate(tr) for tr in tracks],
        )

    def _ensure_artist_exists(self, artist_id: int) -> None:
        if self.db.get(Artist, artist_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Nghệ sĩ (artist_id) không tồn tại",
            )

    def create_album(self, data: AlbumCreate) -> Album:
        """Quản trị viên tạo album mới (UC-15)."""
        self._ensure_artist_exists(data.artist_id)
        duplicate = self.db.scalar(
            select(Album).where(
                Album.artist_id == data.artist_id,
                func.lower(Album.title) == data.title.lower(),
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Album này đã tồn tại cho nghệ sĩ đã chọn",
            )
        return self._commit_and_refresh(Album(title=data.title, artist_id=data.artist_id))

    def update_album(self, album_id: int, data: AlbumUpdate) -> Album:
        """Quản trị viên cập nhật album (UC-15)."""
        album = self.db.get(Album, album_id)
        if album is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album không tồn tại",
            )
        self._ensure_artist_exists(data.artist_id)
        duplicate = self.db.scalar(
            select(Album).where(
                Album.artist_id == data.artist_id,
                func.lower(Album.title) == data.title.lower(),
                Album.album_id != album_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Album này đã tồn tại cho nghệ sĩ đã chọn",
            )
        album.title = data.title
        album.artist_id = data.artist_id
        return self._commit_and_refresh(album)

    def delete_album(self, album_id: int) -> None:
        """Xóa album; chặn nếu đang có bài hát tham chiếu theo BR-04 (UC-15)."""
        album = self.db.get(Album, album_id)
        if album is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album không tồn tại",
            )
        has_track = self.db.scalar(
            select(Track.track_id).where(Track.album_id == album_id).limit(1)
        )
        if has_track is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa album đang có bài hát tham chiếu",
            )
        self._delete_and_commit(album)

    # -------------------------------------------------------------------------
    # Genres
    # -------------------------------------------------------------------------

    def list_genres(
        self,
        page: int = 1,
        page_size: int = 20,
        q: Optional[str] = None,
    ) -> PaginatedResponse[GenreResponse]:
        """Lấy danh sách thể loại nhạc có phân trang (UC-04)."""
        query = select(Genre)
        count_query = select(func.count()).select_from(Genre)
        if q is not None and q.strip():
            cond = build_vi_contains_filter(Genre.name, q)
            query = query.where(cond)
            count_query = count_query.where(cond)

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        genres = list(
            self.db.scalars(
                query.order_by(Genre.name.asc(), Genre.genre_id.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return PaginatedResponse[GenreResponse](
            items=[GenreResponse.model_validate(g) for g in genres],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_genre_by_id(self, genre_id: int) -> Genre:
        """Xem chi tiết một thể loại nhạc (UC-04)."""
        genre = self.db.get(Genre, genre_id)
        if genre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thể loại không tồn tại",
            )
        return genre

    def create_genre(self, data: GenreCreate) -> Genre:
        """Quản trị viên tạo thể loại nhạc mới (UC-15)."""
        duplicate = self.db.scalar(
            select(Genre).where(func.lower(Genre.name) == data.name.lower())
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên thể loại đã tồn tại",
            )
        return self._commit_and_refresh(Genre(name=data.name))

    def update_genre(self, genre_id: int, data: GenreUpdate) -> Genre:
        """Quản trị viên cập nhật tên thể loại nhạc (UC-15)."""
        genre = self.get_genre_by_id(genre_id)
        duplicate = self.db.scalar(
            select(Genre).where(
                func.lower(Genre.name) == data.name.lower(),
                Genre.genre_id != genre_id,
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên thể loại đã tồn tại",
            )
        genre.name = data.name
        return self._commit_and_refresh(genre)

    def delete_genre(self, genre_id: int) -> None:
        """Xóa thể loại; chặn nếu đang có bài hát tham chiếu theo BR-04 (UC-15)."""
        genre = self.get_genre_by_id(genre_id)
        has_track = self.db.scalar(
            select(Track.track_id).where(Track.genre_id == genre_id).limit(1)
        )
        if has_track is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa thể loại đang có bài hát tham chiếu",
            )
        self._delete_and_commit(genre)

    # -------------------------------------------------------------------------
    # Media Types
    # -------------------------------------------------------------------------

    def list_media_types(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[MediaTypeResponse]:
        """Lấy danh sách định dạng âm thanh có phân trang (UC-04)."""
        total = self.db.scalar(select(func.count()).select_from(MediaType)) or 0
        offset = (page - 1) * page_size
        media_types = list(
            self.db.scalars(
                select(MediaType)
                .order_by(MediaType.media_type_id.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return PaginatedResponse[MediaTypeResponse](
            items=[MediaTypeResponse.model_validate(mt) for mt in media_types],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_media_type_by_id(self, media_type_id: int) -> MediaType:
        """Xem chi tiết một định dạng âm thanh (UC-04)."""
        media_type = self.db.get(MediaType, media_type_id)
        if media_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Định dạng âm thanh không tồn tại",
            )
        return media_type
