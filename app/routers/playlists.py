"""[NGƯỜI A] Router /api/v1/playlists (UC-06..UC-12, UC-17)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_admin
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistDetail,
    PlaylistSummary,
    PlaylistTrackAdd,
    PlaylistTrackResponse,
    PlaylistUpdate,
)
from app.services.playlist_service import PlaylistService

router = APIRouter()

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistDetail,
    summary="Tạo playlist mới",
)
def create_playlist(
    data: PlaylistCreate,
    current_user: AppUser = Depends(get_current_user),
    db:Session = Depends(get_db),
) -> Playlist:
    return PlaylistService(db).create_playlist(current_user, data)
# Nhóm định nghĩa /me trước @router.get("/{playlist_id}") để FastAPI không hiểu nhầm chữ "me" là playlist_id (gây lỗi 422).
@router.get(
    "/me",
    response_model=PaginatedResponse,
    summary="Xem danh sách playlist của tôi (UC-07)",
)
def list_my_playlist(
    page: int = Query(1, ge=1),
    page_size: int = Query(20,ge=1, le=100),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlaylistSummary]:
    """Lấy danh sách playlist của người dùng hiện tại."""
    service = PlaylistService(db)
    return service.list_my_playlists(current_user, page, page_size)
@router.get(
    "",
    response_model=PaginatedResponse[PlaylistSummary],
    summary="Admin xem toàn bộ playlist để kiểm duyệt (UC-17)",
)
def list_all_playlists_admin(
    user_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlaylistSummary]:
    return PlaylistService(db).list_all_playlists_admin(
        user_id=user_id, page=page, page_size=page_size
    )
@router.get("/{playlist_id}",
            response_model=PlaylistDetail,
            summary="Lấy chi tiết playlist (UC-07, UC-17)",
)
def get_playlist_detail(
    playlist_id: int,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaylistDetail:
    """Lấy chi tiết playlist."""
    service = PlaylistService(db)
    return service.get_playlist_detail(current_user, playlist_id)
@router.put(
    "/{playlist_id}",
    response_model=PlaylistSummary,
    summary="Cập nhật tên/mô tả playlist (UC-08)",
)
def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Playlist:
    return PlaylistService(db).update_playlist(current_user, playlist_id, data)


@router.delete(
    "/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa playlist (UC-09, UC-17)",
)
def delete_playlist(
    playlist_id: int,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    PlaylistService(db).delete_playlist(current_user, playlist_id)


@router.post(
    "/{playlist_id}/tracks",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistTrackResponse,
    summary="Thêm bài hát vào playlist (UC-10)",
)
def add_track_to_playlist(
    playlist_id: int,
    data: PlaylistTrackAdd,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaylistTrack:
    return PlaylistService(db).add_track_to_playlist(
        current_user, playlist_id, data.track_id
    )

@router.delete(
    "/{playlist_id}/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Gỡ bài hát khỏi playlist (UC-11)",
)
def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    PlaylistService(db).remove_track_from_playlist(
        current_user, playlist_id, track_id
    )