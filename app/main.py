"""[PHẦN CHUNG] Điểm khởi chạy ứng dụng FastAPI và đăng ký các Router."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
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
def health_check() -> dict[str, str]:
    """Kiểm tra nhanh trạng thái hoạt động của API Server."""
    return {"status": "ok", "project": settings.PROJECT_NAME}


app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(tracks.router, prefix=f"{settings.API_V1_STR}/tracks", tags=["Tracks"])
app.include_router(catalog.router, prefix=settings.API_V1_STR, tags=["Catalog"])
app.include_router(playlists.router, prefix=f"{settings.API_V1_STR}/playlists", tags=["Playlists"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/me/history", tags=["History"])
