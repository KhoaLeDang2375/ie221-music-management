"""[NGƯỜI A] Pydantic Schemas cho Đăng ký và Đăng nhập (UC-01, UC-02, UC-05)."""
from pydantic import BaseModel, EmailStr, Field

class UserRegisterRequest(BaseModel):
    """Định nghĩa dữ liệu đầu vào khi đăng ký theo như (UC-01)"""
    username: str = Field(...,min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1,max_length=120)
    password: str = Field(..., min_length=8, max_length=72) # Vì nhóm đã định nghĩa thuật toán băm là 72 token
    

class TokenResponse(BaseModel):
    """Phản hồi JWT access token khi đăng nhập thành công theo như (UC-02)"""
    access_token: str
    token_type: str = "bearer"