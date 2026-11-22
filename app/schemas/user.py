"""[NGƯỜI A] Pydantic Schemas cho Quản lý tài khoản (UC-05, UC-16)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Literal, Optional

class UserResponse(BaseModel):
    """Định nghĩa cấu trúc Response thông tin tài khoản về cho Client"""
    user_id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserAdminUpdate(BaseModel):
    """
        Nhóm định nghĩa cấu trúc dữ liệu để cập nhật trạng thái tài khoản
        (UC-16)
    """
    role: Optional[Literal["user","admin"]] = None
    is_active: Optional[bool] = None
    

