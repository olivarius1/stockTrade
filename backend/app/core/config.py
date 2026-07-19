"""应用配置模块，通过环境变量和 .env 文件加载配置。

关键配置项：
- DATABASE_URL: PostgreSQL 数据库连接地址
- REDIS_URL: Redis 连接地址（缓存和 Celery 消息队列共用）
- SECRET_KEY: JWT 签名密钥（生产环境必须修改）
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Stock Valuation System"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/valuation"
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"

settings = Settings()
