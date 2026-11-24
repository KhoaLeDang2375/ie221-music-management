"""[NGƯỜI B] Lớp HistoryService xử lý nghiệp vụ Lịch sử nghe gần đây (UC-13)."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.catalog import Track
from app.models.history import ListeningHistory
from app.models.user import AppUser
from app.services.base import BaseService


class HistoryService(BaseService):
    """Ghi nhận và truy vấn lịch sử nghe nhạc gần đây của người dùng."""

    def record_listen(self, user: AppUser, track_id: int) -> ListeningHistory:
        """Ghi nhận một lượt nghe bài hát cho người dùng hiện tại (UC-13)."""
        if self.db.get(Track, track_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bài hát không tồn tại trong thư viện",
            )
        entry = ListeningHistory(user_id=user.user_id, track_id=track_id)
        saved = self._commit_and_refresh(entry)
        loaded = self.db.scalar(
            select(ListeningHistory)
            .options(joinedload(ListeningHistory.track))
            .where(ListeningHistory.history_id == saved.history_id)
        )
        assert loaded is not None
        return loaded

    def get_recent_history(
        self,
        user: AppUser,
        limit: int = 20,
    ) -> list[ListeningHistory]:
        """Lấy danh sách các bài hát người dùng nghe gần đây nhất (UC-13)."""
        return list(
            self.db.scalars(
                select(ListeningHistory)
                .options(joinedload(ListeningHistory.track))
                .where(ListeningHistory.user_id == user.user_id)
                .order_by(
                    ListeningHistory.listened_at.desc(),
                    ListeningHistory.history_id.desc(),
                )
                .limit(limit)
            ).all()
        )
