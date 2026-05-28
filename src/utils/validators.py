from fastapi import UploadFile

from src.config import settings
from src.exceptions import ValidationError, FileSizeError


async def validate_file(file: UploadFile) -> UploadFile:
    """Валидация файла"""
    if file.content_type not in settings.allowed_content_types:
        raise ValidationError(
            f"Неподдерживаемый тип файла. Поддерживаемые: {', '.join(settings.allowed_content_types)}",
            detail={"content_type": file.content_type},
        )
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise FileSizeError(settings.max_file_size_mb)
    return file
