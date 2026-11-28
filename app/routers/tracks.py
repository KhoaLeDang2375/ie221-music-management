"""[NGƯỜI B] Router /api/v1/tracks (UC-03, UC-14)."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.track import TrackCreate, TrackDetail, TrackSummary, TrackUpdate
from app.services.track_service import TrackService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TrackSummary],
    summary="Tìm kiếm, lọc, sắp xếp và phân trang bài hát (UC-03)",
)
def search_tracks(
    q: Optional[str] = Query(None, description="Từ khóa tên bài hát"),
    artist_id: Optional[int] = Query(None, ge=1),
    album_id: Optional[int] = Query(None, ge=1),
    genre_id: Optional[int] = Query(None, ge=1),
    sort_by: Literal["name", "duration_ms"] = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TrackSummary]:
    """Tìm kiếm và phân trang danh sách bài hát công khai cho mọi người dùng.

    Args:
        q: Từ khóa tên bài hát cần tìm.
        artist_id: Mã nghệ sĩ cần lọc.
        album_id: Mã album cần lọc.
        genre_id: Mã thể loại cần lọc.
        sort_by: Cột sắp xếp ("name" hoặc "duration_ms").
        order: Chiều sắp xếp ("asc" hoặc "desc").
        page: Số trang hiện tại (>= 1).
        page_size: Số bài hát mỗi trang (1-100).
        db: Session kết nối PostgreSQL.

    Returns:
        Danh sách bài hát có phân trang (PaginatedResponse[TrackSummary]).
    """
    return TrackService(db).search_tracks(
        q=q,
        artist_id=artist_id,
        album_id=album_id,
        genre_id=genre_id,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{track_id}",
    response_model=TrackDetail,
    summary="Xem chi tiết bài hát (UC-03)",
)
def get_track_detail(
    track_id: int,
    db: Session = Depends(get_db),
) -> TrackDetail:
    """Xem thông tin chi tiết một bài hát theo ID.

    Args:
        track_id: Mã bài hát cần xem.
        db: Session kết nối PostgreSQL.

    Returns:
        Thông tin chi tiết bài hát (TrackDetail).
    """
    return TrackService(db).get_track_detail(track_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TrackDetail,
    summary="Quản trị viên thêm bài hát mới (UC-14)",
)
def create_track(
    data: TrackCreate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TrackDetail:
    """Quản trị viên thêm một bài hát mới vào thư viện.

    Args:
        data: Dữ liệu bài hát mới (TrackCreate).
        _: Kiểm tra người gọi có vai trò admin.
        db: Session kết nối PostgreSQL.

    Returns:
        Thông tin chi tiết bài hát vừa tạo (TrackDetail).
    """
    return TrackService(db).create_track(data)


@router.put(
    "/{track_id}",
    response_model=TrackDetail,
    summary="Quản trị viên cập nhật bài hát (UC-14)",
)
def update_track(
    track_id: int,
    data: TrackUpdate,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TrackDetail:
    """Quản trị viên cập nhật toàn bộ thuộc tính của bài hát.

    Args:
        track_id: Mã bài hát cần cập nhật.
        data: Dữ liệu thuộc tính mới (TrackUpdate).
        _: Kiểm tra người gọi có vai trò admin.
        db: Session kết nối PostgreSQL.

    Returns:
        Thông tin chi tiết bài hát sau khi cập nhật (TrackDetail).
    """
    return TrackService(db).update_track(track_id, data)


@router.delete(
    "/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quản trị viên xóa bài hát (UC-14, BR-04)",
)
def delete_track(
    track_id: int,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Quản trị viên xóa bài hát và tự động gỡ khỏi mọi playlist.

    Args:
        track_id: Mã bài hát cần xóa.
        _: Kiểm tra người gọi có vai trò admin.
        db: Session kết nối PostgreSQL.

    Returns:
        Phản hồi rỗng với mã HTTP 204 No Content.
    """
    TrackService(db).delete_track(track_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
