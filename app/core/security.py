"""[PHẦN CHUNG] Các hàm băm mật khẩu bcrypt và tạo/giải mã JWT token."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings



# 1. Xử lý Mật khẩu 

def get_password_hash(password: str) -> str:
    """Băm mật khẩu thô thành chuỗi bcrypt hash để lưu vào DB."""
    # Bcrypt chỉ nhận tối đa 72 bytes
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So khớp mật khẩu thô với chuỗi bcrypt hash trong CSDL."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False



# 2. Xử lý JWT Token (Tạo & Giải mã)

def create_access_token(
    subject: Union[str, int],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo JWT access token chứa subject (user_id/username), vai trò (role) và thời hạn."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Giải mã và xác thực token JWT.
    
    Trả về payload dict nếu hợp lệ, None nếu token hết hạn hoặc sai chữ ký.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
