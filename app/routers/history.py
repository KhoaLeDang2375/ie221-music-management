"""[NGƯỜI B] Router /api/v1/me/history (UC-13)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.history import ListeningHistory
from app.models.user import AppUser
from app.schemas.history import HistoryCreateRequest, HistoryItemResponse
from app.services.history_service import HistoryService

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=HistoryItemResponse,
    summary="Ghi nhận lượt nghe bài hát (UC-13)",
)
def record_listen(
    data: HistoryCreateRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningHistory:
    """Người dùng đã đăng nhập ghi nhận vừa nghe một bài hát.

    Args:
        data: Dữ liệu đầu vào chứa track_id (HistoryCreateRequest).
        current_user: Người dùng hiện tại lấy từ JWT token.
        db: Session kết nối PostgreSQL.

    Returns:
        Bản ghi lịch sử vừa tạo kèm thông tin bài hát (HistoryItemResponse).
    """
    return HistoryService(db).record_listen(current_user, data.track_id)


@router.get(
    "",
    response_model=list[HistoryItemResponse],
    summary="Xem lịch sử nghe gần đây (UC-13)",
)
def get_recent_history(
    limit: int = Query(20, ge=1, le=50),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ListeningHistory]:
    """Lấy tối đa 50 (mặc định 20) lượt nghe gần nhất của chính mình.

    Args:
        limit: Số lượng bản ghi tối đa cần lấy (1-50, mặc định 20).
        current_user: Người dùng hiện tại lấy từ JWT token.
        db: Session kết nối PostgreSQL.

    Returns:
        Danh sách các lượt nghe gần nhất (list[HistoryItemResponse]).
    """
    return HistoryService(db).get_recent_history(current_user, limit=limit)
