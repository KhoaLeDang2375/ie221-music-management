"""[NGƯỜI A] Lớp PlaylistService xử lý nghiệp vụ UC-06..UC-11, UC-17."""
from pydantic import HttpUrl
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.catalog import Track
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistDetail,
    PlaylistSummary,
    PlaylistTrackItem,
    PlaylistUpdate,
)
from app.services.base import BaseService

class PlaylistService(BaseService):
    """Xử lý việc quản lý playlist của người dùng và phục vụ kiểm duyệt"""

    def _get_and_check_access(
        self,
        actor: AppUser,
        playlist_id: int,
        write_mode: bool = False,
    ) -> Playlist:
        """Hàm nhận vào dữ liệu người dùng và playlist để kiểm tra quyền"""
        playlist = self.db.get(Playlist, playlist_id)
        if playlist_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy playlist",
            )
        # biến kiểm tra đúng là owner của playlist không
        is_owner = playlist.user_id == actor.user_id
        if write_mode:
            if not is_owner:
                raise HTTPException(
                    status_code =status.HTTP_403_FORBIDDEN,
                    detail="Chỉ chủ sở hữu mới có quyền sửa playlist này",
                )
        elif not is_owner and actor.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập playlist này",
            )
        return playlist
    def _check_duplicate_name(
        self,
        user_id: int,
        name: str,
        exclude_playlist_id: Optional[int] = None
    ) -> None:
        """Kiểm tra sự trùng lắp tên playlist trong cùng 1 tài khoản dựa vào (BR-05)"""
        query = select(Playlist).where(
            Playlist.user_id == user_id,
            Playlist.name == name,
        )
        # Dùng để phân biệt khi update playlist mà người dùng cần giữ nguyên tên
        if exclude_playlist_id is not None:
            query = query.where(Playlist.playlist_id != exclude_playlist_id)

        # Nếu trùng tên thì raise lỗi
        if self.db.scalar(query) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bạn đã có tên playlist này rồi",
            )
    def create_playlist(self, user: AppUser, data: PlaylistCreate):
        """Hàm nhận vào thông tin user và playlist -> tạo playlist"""
        self._check_duplicate_name(user.user_id, data.name)
        playlist = Playlist(
            name=data.name,
            description=data.description,
            user_id=user.user_id,
        )
        return self._commit_and_refresh(playlist)
    def list_my_playlists(
        self,
        user: AppUser,
        page: int =1,
        page_size: int = 20,
    )->PaginatedResponse[PlaylistSummary]:
        """Lay danh sach playlist cua chinh nguoi dung theo(UC-07)"""
        return self._paginate_playlists(
            user_id=user.user_id, page=page, page_size=page_size
        )
    
    def list_all_playlists_admin(
        self,
        user_id: Optional[int] = None,
        page:  int =1,
        page_size: int = 20,
    ) -> PaginatedResponse[PlaylistSummary]:
        """Ham thuc hien chuc nang cho phep admin xem toan bo 
                playlist de kiem duyet(UC-17)"""
        return self._paginate_playlists(
            user_id = user_id,
            page=page,
            page_size= page_size
        )
    def _paginate_playlists(
        self,
        user_id: Optional[int],
        page: int,
        page_size: int,
    ) -> PaginatedResponse[PlaylistSummary]:
        """Ham thuc hien chuc nang truy van playlist duoi database"""
        query = select(Playlist) # Thuc hien định nghĩa query chưa chạy
        count_query = select(func.count()).select_from(Playlist)

        if user_id is not None:
            query = query.where(Playlist.user_id == user_id)
            count_query = count_query.where(Playlist.user_id == user_id)
        total = self.db.scalar(count_query) or 0
        offset = (page-1)*page_size
        playlists = list(
            self.db.scalars(
                query.order_by(Playlist.playlist_id.desc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        items = [PlaylistSummary.model_validate(pl) for pl in playlists]
        return PaginatedResponse[PlaylistSummary](
            items=items, total=total, page=page, page_size=page_size
        )
    def get_playlist_detail(
        self, actor: AppUser, playlist_id: int
    )-> PlaylistDetail:
        """Ham nay thực hiện viejecc cho phép xem chi tiết playlist (UC-07, UC-13) """
        playlist = self._get_and_check_access(actor,playlist_id,write_mode=False)

        links = list(
            self.db.scalars(
                select(PlaylistTrack)
                .options(selectinload(PlaylistTrack.track))
                .where(PlaylistTrack.playlist_id == playlist.playlist_id)
                .order_by(PlaylistTrack.added_at.asc())
            ).all()
        )

        tracks = [
            PlaylistTrackItem(
                track_id=link.track.track_id,
                name=link.track.name,
                duration_ms=link.track.duration_ms,
                composer=link.track.composer,
                added_at=link.added_at,
            )
            for link in links
        ]

        return PlaylistDetail(
            playlist_id=playlist.playlist_id,
            name=playlist.name,
            description=playlist.description,
            user_id=playlist.user_id,
            created_at=playlist.created_at,
            tracks=tracks,
        )
    def update_playlist(
        self, user: AppUser, playlist_id: int, data: PlaylistUpdate
    ) -> Playlist:
        """Hàm nhận vào dữ liệu để cập nhật tên hoặc mô tả playlisr (UC-08, chỉ chủ sở hữu)"""
        # Kiểm tra quyền
        playlist = self._get_and_check_access(user,playlist_id,write_mode=True)

        # Kiem tra va cap nhat ten
        if data.name is not None and data.name != playlist.name:
            self._check_duplicate_name(
                user.user_id, data.name, exclude_playlist_id=playlist_id
            )
            playlist.name = data.name
        if data.description is not None:
            playlist.description = data.description
        
        return self._commit_and_refresh(playlist)
    
    def delete_playlist(self, actor: AppUser, playlist_id: int) -> None:
        """Xoa Playlist theo (UC-09, UC-17): chu so hu va admin moi co quyen xoa"""
        # Kiem tra quyen
        playlist = self._get_and_check_access(actor, playlist_id, write_mode=False)
        self._delete_and_commit(playlist)
    
    def add_track_to_playlist(
        self, user: AppUser, playlist_id: int, track_id: int
    ) -> PlaylistTrack:
        """Hàm nhận vào id bài hát để thêm vào playlist tương ứng"""

        self._get_and_check_access(user, playlist_id, write_mode= True)

        if self.db.get(Track, track_id) is None:
            raise HTTPException(
                status_code =status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Bài hát không tồn tại trong thư viện",
            )
        
        existing = self.db.get(PlaylistTrack,(playlist_id,track_id))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bài hát đã có trong playlist"
            )
        link = PlaylistTrack(playlist_id=playlist_id, track_id=track_id)
        return self._commit_and_refresh(link)

    def remove_track_from_playlist(
        self, user: AppUser, playlist_id: int, track_id: int
    ) -> None:
        """Hàm thực hiện nhiệm vụ gỡ bài hát ra khỏi playlist"""
        self._get_and_check_access(user, playlist_id, write_mode = True)

        link  = self.db.get(PlaylistTrack, (playlist_id,track_id))
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài hát không nằm trong playlist",
            )
        self._delete_and_commit(link)
    