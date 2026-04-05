from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/crawlscheduler.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Timezone
    TIMEZONE: str = "Asia/Shanghai"

    # Paths
    LOGS_DIR: Path = Path("./data/logs")

    # Scheduler
    SCHEDULER_ENABLED: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production-please"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365  # 1 year
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()

# Create directories if they don't exist
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
