"""[PHẦN CHUNG] Lớp ORM AppUser ánh xạ bảng app_user."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.history import ListeningHistory
    from app.models.playlist import Playlist


class AppUser(Base):
    """Thực thể người dùng hệ thống (bảng app_user)."""

    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="app_user_role_check"),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    playlists: Mapped[list["Playlist"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    listening_histories: Mapped[list["ListeningHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
