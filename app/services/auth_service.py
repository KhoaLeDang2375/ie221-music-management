"""[NGƯỜI A] Lớp AuthService xử lý nghiệp vụ UC-01, UC-02, UC-05."""
from fastapi import HTTPException, status
from sqlalchemy import or_, select

from app.core.security import(
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import AppUser
from app.schemas.auth import TokenResponse, UserRegisterRequest
from app.services.base import BaseService

class AuthService(BaseService):
    """Định nghĩa class dành cho xử lý đăng ký/nhập và lấy thông tin cá nhân"""
    def register(self, data: UserRegisterRequest) -> AppUser:
        """ Đăng ký tài khoản người dùng mới em dựa trên (UC-01, BR-01, BR-09)"""
        # Kiểm tra user có tồn tài chưa ?
        existing_user = self.db.scalar(
            select(AppUser).where(
                or_(
                    AppUser.username == data.username,
                    AppUser.email == data.email,
                )
            )
        )
        # Nếu đã tồn tại
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập hoặc email đã tồn tại",
            )
        # Nếu chưa tồn tại thì tạo user mới

        new_user = AppUser(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            password_hash = get_password_hash(data.password),
            role="user",
            is_active=True
        )
        return self._commit_and_refresh(new_user)
    def login(self, username: str, password: str) -> TokenResponse:
        """Hàm này dùng để xác thực đăng nhập và cấp JWT
            Input: Nhận vào username , password
            Output: Trả về token cho user
        """
        user = self.db.scalar(
            select(AppUser).where(AppUser.username == username)
        )

        # Nếu không có user name hoặc xác thực password không khớp
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không khớp",
                headers = {"WWW-Authenticate": "Bearer"},
            )
        # Nếu user đã bị block
        if not user.is_active:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Tài khoản của bạn đã bị khóa",
            )
        # Cung cấp token
        access_token = create_access_token(subject=user.user_id,role=user.role)
        return TokenResponse(access_token=access_token)
    def get_my_profile(self, current_user : AppUser):
        """
             Tra ve thong tin ca nhan cua user         
        """
        return current_user