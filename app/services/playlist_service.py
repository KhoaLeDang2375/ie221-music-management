"""[NGƯỜI A] Lớp PlaylistService xử lý nghiệp vụ UC-06..UC-11, UC-17."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.models.catalog import Track
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistDetail,
    PlaylistSummary,
    PlaylistUpdate,
)
from app.services.base import BaseService


class PlaylistService(BaseService):
    """Quản lý playlist cá nhân, kiểm duyệt quản trị viên và bài hát trong playlist."""

    def _get_and_check_access(
        self,
        actor: AppUser,
        playlist_id: int,
        write_mode: bool,
        load_tracks: bool = False,
    ) -> Playlist:
        """Lấy playlist và kiểm tra quyền sở hữu / kiểm duyệt theo BR-02."""
        if load_tracks:
            playlist = self.db.scalar(
                select(Playlist)
                .options(selectinload(Playlist.track_links).joinedload(PlaylistTrack.track))
                .where(Playlist.playlist_id == playlist_id)
            )
        else:
            playlist = self.db.get(Playlist, playlist_id)

        if playlist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist không tồn tại",
            )

        is_owner = actor.user_id == playlist.user_id
        if write_mode:
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Chỉ chủ sở hữu mới có quyền chỉnh sửa playlist này",
                )
        elif not is_owner and actor.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập playlist của người khác",
            )

        return playlist

    def create_playlist(self, user: AppUser, data: PlaylistCreate) -> Playlist:
        """Tạo playlist mới thuộc quyền sở hữu của người gọi (UC-06, BR-05)."""
        duplicate = self.db.scalar(
            select(Playlist).where(
                Playlist.user_id == user.user_id,
                func.lower(Playlist.name) == data.name.lower(),
            )
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bạn đã có một playlist với tên này",
            )
        playlist = Playlist(
            name=data.name,
            description=data.description,
            user_id=user.user_id,
        )
        return self._commit_and_refresh(playlist)

    def _paginate_playlists(
        self,
        user_id: Optional[int],
        page: int,
        page_size: int,
    ) -> PaginatedResponse[PlaylistSummary]:
        query = select(Playlist)
        count_query = select(func.count()).select_from(Playlist)
        if user_id is not None:
            query = query.where(Playlist.user_id == user_id)
            count_query = count_query.where(Playlist.user_id == user_id)

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * page_size
        playlists = list(
            self.db.scalars(
                query.order_by(Playlist.playlist_id.desc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )
        return PaginatedResponse[PlaylistSummary](
            items=[PlaylistSummary.model_validate(pl) for pl in playlists],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_my_playlists(
        self,
        user: AppUser,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[PlaylistSummary]:
        """Xem danh sách playlist của chính người dùng đang đăng nhập (UC-07)."""
        return self._paginate_playlists(user_id=user.user_id, page=page, page_size=page_size)

    def list_all_playlists_admin(
        self,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[PlaylistSummary]:
        """Quản trị viên xem toàn bộ playlist để kiểm duyệt, có thể lọc theo chủ sở hữu (UC-17)."""
        return self._paginate_playlists(user_id=user_id, page=page, page_size=page_size)

    def get_playlist_detail(self, actor: AppUser, playlist_id: int) -> PlaylistDetail:
        """Xem chi tiết một playlist kèm danh sách bài hát bên trong (UC-07, UC-17)."""
        playlist = self._get_and_check_access(
            actor, playlist_id, write_mode=False, load_tracks=True
        )
        return PlaylistDetail.from_orm_playlist(playlist)

    def update_playlist(
        self,
        user: AppUser,
        playlist_id: int,
        data: PlaylistUpdate,
    ) -> Playlist:
        """Chủ sở hữu sửa tên và/hoặc mô tả playlist (UC-08, BR-02, BR-05)."""
        playlist = self._get_and_check_access(user, playlist_id, write_mode=True)

        if "name" in data.model_fields_set:
            if data.name is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Tên playlist không được để trống",
                )
            duplicate = self.db.scalar(
                select(Playlist).where(
                    Playlist.user_id == user.user_id,
                    func.lower(Playlist.name) == data.name.lower(),
                    Playlist.playlist_id != playlist_id,
                )
            )
            if duplicate is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bạn đã có một playlist khác với tên này",
                )
            playlist.name = data.name

        if "description" in data.model_fields_set:
            playlist.description = data.description

        return self._commit_and_refresh(playlist)

    def delete_playlist(self, actor: AppUser, playlist_id: int) -> None:
        """Chủ sở hữu hoặc quản trị viên xóa playlist (UC-09, UC-17, BR-02)."""
        playlist = self._get_and_check_access(actor, playlist_id, write_mode=False)
        self._delete_and_commit(playlist)

    def add_track_to_playlist(
        self,
        user: AppUser,
        playlist_id: int,
        track_id: int,
    ) -> PlaylistTrack:
        """Chủ sở hữu thêm bài hát vào playlist, không cho phép trùng bài (UC-10, BR-03)."""
        self._get_and_check_access(user, playlist_id, write_mode=True)

        if self.db.get(Track, track_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Bài hát (track_id) không tồn tại trong thư viện",
            )

        existing_link = self.db.get(PlaylistTrack, (playlist_id, track_id))
        if existing_link is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bài hát đã tồn tại trong playlist",
            )

        link = PlaylistTrack(playlist_id=playlist_id, track_id=track_id)
        self._commit_and_refresh(link)
        loaded = self.db.scalar(
            select(PlaylistTrack)
            .options(joinedload(PlaylistTrack.track))
            .where(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id,
            )
        )
        assert loaded is not None
        return loaded

    def remove_track_from_playlist(
        self,
        user: AppUser,
        playlist_id: int,
        track_id: int,
    ) -> None:
        """Chủ sở hữu gỡ một bài hát khỏi playlist (UC-11, BR-02)."""
        self._get_and_check_access(user, playlist_id, write_mode=True)
        link = self.db.get(PlaylistTrack, (playlist_id, track_id))
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài hát không nằm trong playlist",
            )
        self._delete_and_commit(link)
