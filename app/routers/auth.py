"""[NGƯỜI A] Router /api/v1/auth (UC-01, UC-02, UC-05)."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.auth import TokenResponse, UserRegisterRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Đăng ký tài khoản mới theo (UC1)"
)
def register(
    data: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> AppUser:
    """
        Hàm dùng tạo user mới
    """
    return AuthService(db).register(data)
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Endpoint này dùng để đăng nhập và lấy JWT token(UC-02)",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
        Hàm dùng đăng nhập và lấy JWT Token
    """
    return AuthService(db).login(form_data.username, form_data.password)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin tài khoản hiện tại(UC-05)"
)
def get_me(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AppUser:
    """
        Hàm dùng lấy thông tin user hiện tại
    """
    return AuthService(db).get_my_profile(current_user)