import logging.config
import os
from pathlib import Path
from typing import List, Set
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта и папка для логов
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # Окружение
    environment: str = "development"
    debug: bool = False

    # Приложение
    app_name: str = "MedLab OCR API"
    api_version: str = "1.0.0"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Настройки базы данных
    db_host: str = "db"
    db_port: int = 5432

    db_user: str
    db_password: str

    db_name: str = "med_db"

    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    redis_password: str | None = None

    redis_cache_ttl: int = 3600

    # File upload
    max_file_size_mb: int = 50
    upload_directory: str = "./uploads"
    allowed_content_types: Set[str] = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
    }

    # OCR service
    ocr_timeout_seconds: int = 30
    ocr_retry_attempts: int = 2
    ocr_retry_delay: float = 0.5
    ocr_language_pack: str = "rus+eng"
    tesseract_path: str = "/usr/bin/tesseract"

    # Внешние API
    gemini_api_key: str

    # Logging
    log_level: str = "INFO"
    log_format: str = "text"  # json / text
    log_file: str = "logs/error.log"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=False,
        extra="ignore"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Создаем экземпляр настроек
settings = Settings()

# Проверяем, запущены ли тесты (чтобы не спамить логами и не падать по правам доступа)
IS_TESTING = os.getenv("TESTING") == "True"

if not IS_TESTING:
    # Гарантируем создание папки для логов относительно корня
    LOG_FILE_PATH = BASE_DIR / settings.log_file
    LOG_FILE_PATH.parent.mkdir(exist_ok=True)

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"
                ),
            },
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.log_format == "json" else "default",
                "level": settings.log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json" if settings.log_format == "json" else "detailed",
                "filename": str(LOG_FILE_PATH),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "level": settings.log_level,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json" if settings.log_format == "json" else "detailed",
                "filename": str(LOG_FILE_PATH),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "level": "ERROR",
            },
        },
        "loggers": {
            "sqlalchemy.engine": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file", "error_file"],
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)
else:
    # Облегченный логгер для тестов (только в консоль, файлы не трогаем)
    logging.basicConfig(level="WARNING")
