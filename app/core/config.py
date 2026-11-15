"""[PHẦN CHUNG] Lớp Settings đọc biến môi trường từ file .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Quản lý cấu hình toàn dự án có thể tái sử dụng thay vì mỗi 
    file phải khai báo lại
    """
    # 1. Thông tin chung 
    PROJECT_NAME: str = "Music Management RESTful API"
    API_V1_STR: str = "/api/v1"
    # 2. Database 
    DATABASE_URL: str
    # 3. JWT Authentication 
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # 4. Chat bot key
    GROQ_API_KEY: str = "" 
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    # Cấu hình nạp từ .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
settings = Settings()