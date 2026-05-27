from fastapi import UploadFile

from src.exceptions import ValidationError, FileSizeError

MAX_FILE_SIZE_MB = 50
ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
    }

async def validate_file(file: UploadFile) -> UploadFile:
    """Валидация файла"""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            f"Неподдерживаемый тип файла. Поддерживаемые: {', '.join(ALLOWED_CONTENT_TYPES)}",
            detail={"content_type": file.content_type},
        )
    if file.size and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileSizeError(MAX_FILE_SIZE_MB)
    return file