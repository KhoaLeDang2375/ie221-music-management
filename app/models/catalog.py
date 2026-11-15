"""[PHẦN CHUNG] Các lớp ORM Artist, Album, Genre, MediaType, Track."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.history import ListeningHistory
    from app.models.playlist import PlaylistTrack


class Artist(Base):
    """Thực thể nghệ sĩ (bảng artist)."""

    __tablename__ = "artist"

    artist_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    albums: Mapped[list["Album"]] = relationship(back_populates="artist")


class Album(Base):
    """Thực thể album nhạc (bảng album)."""

    __tablename__ = "album"

    album_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artist.artist_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    artist: Mapped["Artist"] = relationship(back_populates="albums")
    tracks: Mapped[list["Track"]] = relationship(back_populates="album")


class Genre(Base):
    """Thực thể thể loại nhạc (bảng genre)."""

    __tablename__ = "genre"

    genre_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    tracks: Mapped[list["Track"]] = relationship(back_populates="genre")


class MediaType(Base):
    """Thực thể định dạng âm thanh (bảng media_type)."""

    __tablename__ = "media_type"

    media_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    tracks: Mapped[list["Track"]] = relationship(back_populates="media_type")


class Track(Base):
    """Thực thể bài hát (bảng track)."""

    __tablename__ = "track"
    __table_args__ = (
        CheckConstraint("duration_ms > 0", name="track_duration_ms_check"),
    )

    track_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    album_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("album.album_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    media_type_id: Mapped[int] = mapped_column(
        ForeignKey("media_type.media_type_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    genre_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("genre.genre_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    composer: Mapped[Optional[str]] = mapped_column(String(220), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    album: Mapped[Optional["Album"]] = relationship(back_populates="tracks")
    media_type: Mapped["MediaType"] = relationship(back_populates="tracks")
    genre: Mapped[Optional["Genre"]] = relationship(back_populates="tracks")
    playlist_links: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )
    listening_histories: Mapped[list["ListeningHistory"]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )
