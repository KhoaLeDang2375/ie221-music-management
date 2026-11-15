"""[PHẦN CHUNG] Lớp cha BaseService đóng gói Session và thao tác transaction."""
# Bới vì các service bên dưới có thao tác lặp lại là kết nối + thao tác database nên nhóm làm sẵn tránh lặp
from typing import TypeVar
from sqlalchemy.orm import Session
from app.db.base import Base
ModelType = TypeVar("ModelType", bound=Base)

class BaseService:
    """Lớp cơ sở cho các lớp xử lý nghiệp vụ"""
    def __init__(self, db: Session) -> None:
        self.db = db
    # Khai bao ham protect cho con truc tiep su dung
    def _commit_and_refresh(self, instance: ModelType) -> ModelType:
        """Lưu mới hoặc cập nhật bản ghi được cung cấp và đồng bộ lại dữ liệu từ DB."""
        try:
            self.db.app(instance)
            # Sau do commit 
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except Exception:
            # Roll back lai trang thai db neu loi
            self.db.rollback()
            raise
    def _delete_and_commit(self, instance: Base) -> None:
        """Xóa bản ghi và xác nhận giao dịch xuống DB."""
        try:
            self.db.delete(instance)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise