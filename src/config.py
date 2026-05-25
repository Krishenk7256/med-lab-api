import logging.config
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # Окружение
    environment: str = "development"
    debug: bool = False

    # Приложение
    app_name: str = "MedLab OCR API"
    api_version: str = "1.0.0"
    secret_key: str = "some-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Это база
    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "med_user"
    db_password: str = "med_password"
    db_name: str = "med_db"
    database_url: str = "" # Ниже будет

    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_url: str = "" # Опять ниже будет
    redis_cache_ttl: int = 3600

    # File upload
    max_file_size_mb: int = 50
    upload_directory: str = "./uploads"
    allowed_extensions: str = "pdf,png,jpg,jpeg,webp,csv,xlsx,xls"

    # OCR service
    ocr_timeout_seconds: int = 30
    ocr_retry_attempts: int = 2
    ocr_retry_delay: float = 0.5
    ocr_language_pack: str = "rus+eng"
    tesseract_path: str = "/usr/bin/tesseract"

    # Внешние API
    # llm_provider: str = "openai"
    # llm_api_key: str = ""
    # llm_model: str = "gpt-4"
    # llm_temperature: float = 0.7
    # llm_max_tokens: int = 500
    #
    # smtp_host: str = "smtp.gmail.com"
    # smtp_port: int = 587
    # smtp_user: str = ""
    # smtp_password: str = ""
    # smtp_from_email: str = "noreply@medlab.com"

    # Logging
    log_level: str = "INFO"
    log_format: str = "text" # json / text
    log_file: str = "logs/error.log"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5

    # Monitoring
    # sentry_dsn: str = ""
    # prometheus_metrics: bool = False
    # jaeger_enabled: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = "../.env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.database_url:
            self.database_url (
                f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        if not self.redis_url:
            auth = f":{self.redis_password}@" if self.redis_password else ""
            self.redis_url = (
                f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )

    @property
    def cors_origins_list(self) -> List[str]:
        """Возвращает список CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Возвращает список разрешённых расширений"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

settings = Settings()

#Конфигурация логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

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
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": settings.log_format if settings.log_format == "json" else "default",
            "level": settings.log_level,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": settings.log_format if settings.log_format == "json" else "detailed",
            "filename": settings.log_file,
            "maxBytes": settings.log_max_bytes,
            "backupCount": settings.log_backup_count,
            "level": settings.log_level,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": settings.log_format if settings.log_format == "json" else "detailed",
            "filename": settings.log_error_file,
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