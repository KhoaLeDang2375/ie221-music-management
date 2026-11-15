"""[PHẦN CHUNG] Các lớp ORM Playlist, PlaylistTrack."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.catalog import Track
    from app.models.user import AppUser


class Playlist(Base):
    """Thực thể danh sách phát cá nhân (bảng playlist)."""

    __tablename__ = "playlist"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="playlist_user_id_name_key"),
        CheckConstraint(
            "char_length(trim(name)) BETWEEN 1 AND 100",
            name="playlist_name_length_check",
        ),
    )

    playlist_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    owner: Mapped["AppUser"] = relationship(back_populates="playlists")
    track_links: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="playlist", cascade="all, delete-orphan"
    )


class PlaylistTrack(Base):
    """Bảng liên kết nhiều-nhiều giữa Playlist và Track (bảng playlist_track)."""

    __tablename__ = "playlist_track"

    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlist.playlist_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("track.track_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    playlist: Mapped["Playlist"] = relationship(back_populates="track_links")
    track: Mapped["Track"] = relationship(back_populates="playlist_links")
