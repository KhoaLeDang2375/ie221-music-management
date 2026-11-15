"""[PHẦN CHUNG] Lớp ORM ListeningHistory ánh xạ bảng listening_history."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, desc, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.catalog import Track
    from app.models.user import AppUser


class ListeningHistory(Base):
    """Thực thể lịch sử nghe nhạc (bảng listening_history)."""

    __tablename__ = "listening_history"
    __table_args__ = (
        Index("listening_history_user_time_idx", "user_id", desc("listened_at")),
    )

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("track.track_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    listened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["AppUser"] = relationship(back_populates="listening_histories")
    track: Mapped["Track"] = relationship(back_populates="listening_histories")
