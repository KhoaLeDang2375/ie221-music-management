"""[NGƯỜI B] Lớp TrackService xử lý nghiệp vụ tìm kiếm và CRUD bài hát (UC-03, UC-14)."""

import unicodedata
from typing import Any, Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import joinedload

from app.models.catalog import Album, Genre, MediaType, Track
from app.schemas.common import PaginatedResponse
from app.schemas.track import TrackCreate, TrackDetail, TrackSummary, TrackUpdate
from app.services.base import BaseService

_VN_ACCENTED = (
    "àáảãạăằắẳẵặâầấẩẫậÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ"
    "èéẻẽẹêềếểễệÈÉẺẼẸÊỀẾỂỄỆ"
    "ìíỉĩịÌÍỈĨỊ"
    "òóỏõọôồốổỗộơờớởỡợÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ"
    "ùúủũụưừứửữựÙÚỦŨỤƯỪỨỬỮỰ"
    "ỳýỷỹỵỲÝỶỸỴ"
    "đĐ"
)
_VN_ASCII = (
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    "eeeeeeeeeeeeeeeeeeeeee"
    "iiiiiiiiii"
    "oooooooooooooooooooooooooooooooooo"
    "uuuuuuuuuuuuuuuuuuuuuu"
    "yyyyyyyyyy"
    "dd"
)
assert len(_VN_ACCENTED) == len(_VN_ASCII)


def normalize_vi_text(text: str) -> str:
    """Chuẩn hóa chuỗi về chữ thường không dấu để tìm kiếm tiếng Việt linh hoạt."""
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d")


def build_vi_contains_filter(column: Any, query_text: str) -> ColumnElement[bool]:
    """Tạo điều kiện SQL LIKE không phân biệt hoa/thường và không dấu tiếng Việt."""
    normalized = normalize_vi_text(query_text)
    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    col_norm = func.lower(func.translate(column, _VN_ACCENTED, _VN_ASCII))
    return col_norm.like(f"%{escaped}%", escape="\\")


class TrackService(BaseService):
    """Xử lý tra cứu, lọc, sắp xếp và quản trị bài hát trong thư viện."""

    def search_tracks(
        self,
        q: Optional[str] = None,
        artist_id: Optional[int] = None,
        album_id: Optional[int] = None,
        genre_id: Optional[int] = None,
        sort_by: Literal["name", "duration_ms"] = "name",
        order: Literal["asc", "desc"] = "asc",
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TrackSummary]:
        """Tìm kiếm, lọc, sắp xếp và phân trang danh sách bài hát (UC-03)."""
        query = select(Track)
        count_query = select(func.count()).select_from(Track)

        if artist_id is not None:
            query = query.join(Track.album).where(Album.artist_id == artist_id)
            count_query = count_query.join(Track.album).where(Album.artist_id == artist_id)

        if album_id is not None:
            query = query.where(Track.album_id == album_id)
            count_query = count_query.where(Track.album_id == album_id)

        if genre_id is not None:
            query = query.where(Track.genre_id == genre_id)
            count_query = count_query.where(Track.genre_id == genre_id)

        if q is not None and q.strip():
            condition = build_vi_contains_filter(Track.name, q)
            query = query.where(condition)
            count_query = count_query.where(condition)

        sort_column = Track.duration_ms if sort_by == "duration_ms" else Track.name
        order_expr = sort_column.desc() if order == "desc" else sort_column.asc()

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        tracks = list(
            self.db.scalars(
                query.order_by(order_expr, Track.track_id.asc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        items = [TrackSummary.model_validate(track) for track in tracks]
        return PaginatedResponse[TrackSummary](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def _get_track_or_404(self, track_id: int, with_relations: bool = False) -> Track:
        """Lấy bản ghi Track theo ID hoặc ném HTTP 404 nếu không tồn tại."""
        if with_relations:
            track = self.db.scalar(
                select(Track)
                .options(
                    joinedload(Track.album).joinedload(Album.artist),
                    joinedload(Track.genre),
                    joinedload(Track.media_type),
                )
                .where(Track.track_id == track_id)
            )
        else:
            track = self.db.get(Track, track_id)

        if track is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài hát không tồn tại",
            )
        return track

    def get_track_detail(self, track_id: int) -> TrackDetail:
        """Xem thông tin chi tiết một bài hát kèm tên album, nghệ sĩ, thể loại (UC-03)."""
        track = self._get_track_or_404(track_id, with_relations=True)
        return TrackDetail.from_orm_track(track)

    def _validate_foreign_keys(
        self,
        album_id: Optional[int],
        genre_id: Optional[int],
        media_type_id: int,
    ) -> None:
        """Kiểm tra khóa ngoại album_id, genre_id, media_type_id có tồn tại trong DB."""
        if self.db.get(MediaType, media_type_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Định dạng âm thanh (media_type_id) không tồn tại",
            )
        if album_id is not None and self.db.get(Album, album_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Album (album_id) không tồn tại",
            )
        if genre_id is not None and self.db.get(Genre, genre_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Thể loại (genre_id) không tồn tại",
            )

    def create_track(self, data: TrackCreate) -> TrackDetail:
        """Quản trị viên thêm bài hát mới vào thư viện (UC-14)."""
        self._validate_foreign_keys(data.album_id, data.genre_id, data.media_type_id)
        track = Track(
            name=data.name,
            album_id=data.album_id,
            media_type_id=data.media_type_id,
            genre_id=data.genre_id,
            composer=data.composer,
            duration_ms=data.duration_ms,
        )
        saved = self._commit_and_refresh(track)
        return self.get_track_detail(saved.track_id)

    def update_track(self, track_id: int, data: TrackUpdate) -> TrackDetail:
        """Quản trị viên cập nhật toàn bộ thông tin bài hát (UC-14)."""
        track = self._get_track_or_404(track_id)
        self._validate_foreign_keys(data.album_id, data.genre_id, data.media_type_id)

        track.name = data.name
        track.album_id = data.album_id
        track.media_type_id = data.media_type_id
        track.genre_id = data.genre_id
        track.composer = data.composer
        track.duration_ms = data.duration_ms

        self._commit_and_refresh(track)
        return self.get_track_detail(track.track_id)

    def delete_track(self, track_id: int) -> None:
        """Quản trị viên xóa bài hát; DB tự động gỡ khỏi mọi playlist theo BR-04 (UC-14)."""
        track = self._get_track_or_404(track_id)
        self._delete_and_commit(track)
