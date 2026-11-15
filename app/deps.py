"""[PHẦN CHUNG] Dependency Injection: get_db, get_current_user, require_admin."""
# Tăng tính tái sử dụng Thay vì ở mỗi API phải tự viết code mở/đóng kết nối DB, tự giải mã JWT rồi tự kiểm tra quyền admin nên mất rất nhiều thời gian
from collections.abc import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import AppUser
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
def get_db() -> Generator[Session, None, None]:
    """Tạo một DB Session cho mỗi request và tự động đóng sau khi xử lý xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AppUser:
    """Giải mã JWT token, truy vấn AppUser và kiểm tra trạng thái hoạt động (BR-06)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    sub = payload.get("sub")
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception
    user = db.get(AppUser, user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )
    return user
def require_admin(
    current_user: AppUser = Depends(get_current_user),
) -> AppUser:
    """Chỉ cho phép người dùng có vai trò 'admin' truy cập (BR-07)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị viên để thực hiện thao tác này",
        )
    return current_user