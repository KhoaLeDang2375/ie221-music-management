"""[PHẦN CHUNG] Điểm khởi chạy ứng dụng FastAPI và đăng ký các Router."""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.deps import get_db
from app.routers import auth, catalog, history, playlists, tracks, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Kiểm tra trạng thái hoạt động của API Server và kết nối PostgreSQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối tới cơ sở dữ liệu PostgreSQL",
        ) from exc
    return {
        "status": "ok",
        "database": "connected",
        "project": settings.PROJECT_NAME,
    }


app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(tracks.router, prefix=f"{settings.API_V1_STR}/tracks", tags=["Tracks"])
app.include_router(catalog.router, prefix=settings.API_V1_STR, tags=["Catalog"])
app.include_router(playlists.router, prefix=f"{settings.API_V1_STR}/playlists", tags=["Playlists"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/me/history", tags=["History"])
