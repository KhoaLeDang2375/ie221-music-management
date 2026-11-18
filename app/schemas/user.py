"""[NGƯỜI A] Pydantic Schemas cho Quản lý tài khoản (UC-05, UC-16)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

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


