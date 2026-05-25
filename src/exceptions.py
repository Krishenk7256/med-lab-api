from typing import Optional, Any, Dict


class APIException(Exception):
    """Базовое исключение под API"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail or {}
        super().__init__(self.message)

class OCRProcessingError(APIException):
    """Ошибка при обработке файла OCR"""
    def __init__(self, message: str, detail: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="OCR_PROCESSING_ERROR",
            detail=detail,
        )

class UnsupportedFileFormatError(OCRProcessingError):
    """Неподдерживаемый формат файла"""
    def __init__(self, content_type: str):
        super().__init__(
            message=f"Неподдерживаемый формат файла: {content_type}",
            error_code="UNSUPPORTED_FILE_FORMAT",
            detail={"content_type": content_type},
        )

class FileParsingError(OCRProcessingError):
    """Ошибка при парсинге конкретного типа файла"""
    def __init__(self, file_type: str, original_error: Exception):
        super().__init__(
            message=f"Ошибка при парсинге {file_type}: {str(original_error)}",
            error_code="FILE_PARSING_ERROR",
            detail={
                "file_type": file_type,
                "original_error": str(original_error),
            },
        )

class FileSizeError(APIException):
    """Файл слишком большой"""
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"Размер файла превышает максимум {max_size_mb}",
            status_code=413,
            detail={"max_size_mb": max_size_mb},
        )

class ValidationError(APIException):
    """Ошибка валидации входных данных"""
    def __init__(self, message: str, detail: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            detail=detail
        )

class DatabaseError(APIException):
    """Ошибка при работе с БД"""
    def __init__(self, message=str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
        )

class LabReportNotFoundError(APIException):
    """Отчёт не найден"""
    def __init__(self, report_id: int):
        super().__init__(
            message=f"Отчёт с ID {report_id} не найден",
            status_code=404,
            error_code="LAB_REPORT_NOT_FOUND",
            detail={"report_id": report_id}
        )


