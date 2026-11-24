"""[NGƯỜI A] Router /api/v1/playlists (UC-06..UC-12, UC-17)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_admin
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import AppUser
from app.schemas.chatbot import ChatbotPlaylistRequest, ChatbotPlaylistResponse
from app.schemas.common import PaginatedResponse
from app.schemas.playlist import (
    PlaylistAddTrackRequest,
    PlaylistCreate,
    PlaylistDetail,
    PlaylistSummary,
    PlaylistTrackItem,
    PlaylistUpdate,
)
from app.services.chatbot_service import ChatbotService, GroqClient
from app.services.playlist_service import PlaylistService

router = APIRouter()


def get_groq_client() -> GroqClient:
    """Dependency cung cấp GroqClient (cho phép override bằng mock khi test)."""
    return GroqClient()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistSummary,
    summary="Tạo playlist cá nhân mới (UC-06)",
)
def create_playlist(
    data: PlaylistCreate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Playlist:
    """Người dùng đã đăng nhập tạo một playlist rỗng mới."""
    return PlaylistService(db).create_playlist(current_user, data)


@router.get(
    "/me",
    response_model=PaginatedResponse[PlaylistSummary],
    summary="Xem danh sách playlist cá nhân của tôi (UC-07)",
)
def list_my_playlists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlaylistSummary]:
    """Lấy danh sách playlist thuộc sở hữu của người đang đăng nhập."""
    return PlaylistService(db).list_my_playlists(
        current_user, page=page, page_size=page_size
    )


@router.get(
    "",
    response_model=PaginatedResponse[PlaylistSummary],
    summary="Quản trị viên xem mọi playlist để kiểm duyệt (UC-17)",
)
def list_all_playlists_admin(
    user_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlaylistSummary]:
    """Quản trị viên xem toàn bộ playlist trong hệ thống, lọc được theo user_id."""
    return PlaylistService(db).list_all_playlists_admin(
        user_id=user_id, page=page, page_size=page_size
    )


@router.post(
    "/generate-ai",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatbotPlaylistResponse,
    summary="Tạo playlist tự động bằng Chatbot Groq AI (UC-12)",
)
def generate_playlist_ai(
    req: ChatbotPlaylistRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    groq_client: GroqClient = Depends(get_groq_client),
) -> ChatbotPlaylistResponse:
    """Nhận mô tả tự nhiên, trích xuất tiêu chí qua Groq và tạo playlist từ thư viện thật."""
    return ChatbotService(db, groq_client=groq_client).generate_playlist_from_prompt(
        current_user, req
    )


@router.get(
    "/{playlist_id}",
    response_model=PlaylistDetail,
    summary="Xem chi tiết playlist kèm danh sách bài hát (UC-07, UC-17)",
)
def get_playlist_detail(
    playlist_id: int,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaylistDetail:
    """Chủ sở hữu hoặc quản trị viên xem chi tiết playlist."""
    return PlaylistService(db).get_playlist_detail(current_user, playlist_id)


@router.put(
    "/{playlist_id}",
    response_model=PlaylistSummary,
    summary="Chủ sở hữu cập nhật tên/mô tả playlist (UC-08)",
)
def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Playlist:
    """Chỉ chủ sở hữu playlist mới có quyền chỉnh sửa nội dung (BR-02)."""
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
) -> Response:
    """Chủ sở hữu hoặc quản trị viên xóa playlist (không xóa bài hát gốc)."""
    PlaylistService(db).delete_playlist(current_user, playlist_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{playlist_id}/tracks",
    status_code=status.HTTP_201_CREATED,
    response_model=PlaylistTrackItem,
    summary="Chủ sở hữu thêm bài hát vào playlist (UC-10)",
)
def add_track_to_playlist(
    playlist_id: int,
    data: PlaylistAddTrackRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaylistTrack:
    """Thêm bài hát vào playlist cá nhân (chặn trùng lặp theo BR-03)."""
    return PlaylistService(db).add_track_to_playlist(
        current_user, playlist_id, data.track_id
    )


@router.delete(
    "/{playlist_id}/tracks/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Chủ sở hữu gỡ bài hát khỏi playlist (UC-11)",
)
def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Gỡ một bài hát khỏi playlist (bài hát vẫn còn trong thư viện)."""
    PlaylistService(db).remove_track_from_playlist(current_user, playlist_id, track_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
