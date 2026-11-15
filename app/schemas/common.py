"""[PHẦN CHUNG] Generic Schema PaginatedResponse[T] dùng chung cho phân trang."""
# Khai báo TypeVar cho kiểu Generic T
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T= TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Cấu trúc phản hồi phân trang chuẩn cho các API danh sách."""
    items: list[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    model_config = ConfigDict(from_attributes=True)
