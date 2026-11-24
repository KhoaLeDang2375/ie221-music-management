"""[PHẦN CHUNG] Cấu hình pytest fixtures dùng chung cho kiểm thử."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import engine
from app.deps import get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Tạo SQLAlchemy Session cô lập bằng savepoint để tự rollback sau mỗi test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Tạo TestClient gắn DB session cô lập (tự rollback mọi thay đổi sau test)."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def get_auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    """Đăng nhập và trả về header Authorization Bearer."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    """Header Bearer token cho tài khoản admin mặc định."""
    return get_auth_headers(client, "admin", "admin@123")


@pytest.fixture()
def user_headers(client: TestClient) -> dict[str, str]:
    """Header Bearer token cho tài khoản user mặc định."""
    return get_auth_headers(client, "testuser", "testuser@123")
