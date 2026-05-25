from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Стандартный формат ошибки в API"""
    error_code: str = Field(..., description="Код Ошибки")
    message: str = Field(..., description="Описание Ошибки")
    status_code: str = Field(..., description="HTTP статус")
    detail: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Дополнительные детали ошибки"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "OCR_PROCESSIGN_ERROR",
                "message": "Ошибка при парсинге PDF: Invalid file structure",
                "status_code": 400,
                "detail": {
                    "file_type": "pdf",
                    "original_error": "Invalid file structure",
                }
            }
        }