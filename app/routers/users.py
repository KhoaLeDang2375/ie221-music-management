"""[NGƯỜI A] Router /api/v1/users (UC-16)."""


from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter()

@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="Xem danh sách tài khoản có phân trang theo (UC-16)",
)
def list_user(
    page: int = Query(1,ge=1),
    page_size: int =Query(20,ge=1, le=100),
    role: Optional[Literal["user","admin"]] = Query(None),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
)->PaginatedResponse[UserResponse]:
    """
    Xem danh sách tài khoản có phân trang theo role.

    Args:
        page: Trang hiện tại (bắt đầu từ 1).
        page_size: Số lượng tài khoản mỗi trang (1-100).
        role: Lọc theo vai trò (user/admin).
        db: Session database.

    Returns:
        Thông tin phân trang kèm danh sách tài khoản.
    """
    return UserService(db).list_user( page=page, page_size=page_size, role=role)
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Xem thông tin chi tiết tài khoản theo ID (UC-16)",
)
def get_user_detail(
    user_id:int,
    _: AppUser = Depends(require_admin),
    db: Session = Depends(get_db)
)->AppUser:
    """Quản trị viên xem thông tin chi tiết một tài khoản."""
    return UserService(db).get_user_by_id(user_id=user_id)

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Cập nhật thông tin tài khoản theo ID (UC-16)"
)
def update_user(
    user_id:int,
    data: UserAdminUpdate,
    current_admin: AppUser = Depends(require_admin),
    db: Session = Depends(get_db)
)->AppUser:
    """Quản trị viên cập nhật thông tin một tài khoản."""
    return UserService(db).update_user_status_or_role(
        admin = current_admin,
        target_id=user_id,
        data=data
    )

