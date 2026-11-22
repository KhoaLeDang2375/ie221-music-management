"""[NGƯỜI A] Lớp UserService xử lý nghiệp vụ quản trị tài khoản UC-16."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.models.user import AppUser
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserResponse
from app.services.base import BaseService

class UserService(BaseService):
    """
        Dùng để xử lý việc xem danh sách, chi tiết và cập nhật quyền/trạng thái 
        tài khoản.
    """
    def list_user(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
    )->PaginatedResponse:
        """
        Hàm đảm nhận việc  lấy danh sách tài khoản có phân trang + lọc theo vai trò
        """
        query = select(AppUser)
        count_query  = select(func.count()).select_from(AppUser)
        # Nhánh bên dưới chạy khi có điều kiện lọc theo role
        if role is not None:
            query = query.where(AppUser.role == role)
            count_query = count_query.where(AppUser.role == role)
        total = self.db.scalar(count_query) or 0
        offset = (page - 1)*page_size
        users = list(
            self.db.scalars(
                query.order_by(AppUser.user_id.asc()).offset(offset).limit(page_size)
            ).all()
        )
        items = [UserResponse.model_validate(user) for user in users]
        return PaginatedResponse[UserResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ) 
    def get_user_by_id(self, user_id: int) -> AppUser:
        """
            Hàm này đảm nhận nhiệm vụ truy vấn user theo id (UC-16)
            input: user_id
            output: Thông tin user
        """
        user = self.db.get(AppUser,user_id)
        # Nếu không lấy được user raise lỗi
        if user is None:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Không tìm thấy tài khoản "
            )
        return user
    def update_user_status_or_role(
        self,
        admin: AppUser,
        target_id: int,
        data: UserAdminUpdate
    )->AppUser:
        """Hàm thực hiện nhiệm vụ cập nhật vai trò đóng hoặc khóa tài khoản"""
        user = self.get_user_by_id(target_id)

        if admin.user_id == target_id:
            if data.is_active is False or (data.role is not None and data.role != "admin"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Quản trị viên không được tự khóa hoặc hạ quyền",
                )
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        
        return self._commit_and_refresh(user)