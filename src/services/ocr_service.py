import io
import logging
import pandas as pd
from pandas import DataFrame
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
from fastapi.concurrency import run_in_threadpool
from fastapi import UploadFile

from src.utils.decorators import retry, log_async_time
from src.exceptions import (
    UnsupportedFileFormatError,
    FileParsingError,
    OCRProcessingError
)


logger = logging.getLogger(__name__)

#@log_sync_time
def parse_pdf(file_bytes: bytes) -> str:
    """Парсинг PDF файла"""
    try:
        images = convert_from_bytes(file_bytes)
        full_text = []
        for image in images:
            text = pytesseract.image_to_string(image, lang="rus+eng")
            full_text.append(text)
        return "".join(full_text)
    except Exception as e:
        logger.error(f"Сбой при парсинге PDF: {str(e)}", exc_info=True)
        raise FileParsingError("pdf", e)

#@log_sync_time
def parse_image(file_bytes: bytes) -> str:
    """Парсинг изображения"""
    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image, lang="rus+eng")
        return text.strip()
    except Exception as e:
        logger.error(f"Сбой при парсинге изображения: {str(e)}", exc_info=True)
        raise FileParsingError("image", e)

#@log_sync_time
def parse_table(file_bytes: bytes, is_csv = False) -> str:
    """Парсинг таблиц (CSV/Excel)"""
    try:
        buffer = io.BytesIO(file_bytes)
        df: DataFrame
        if is_csv:
            df = pd.read_csv(buffer) # type: ignore
        else:
            df = pd.read_excel(buffer)
        return df.to_string(index = False)
    except Exception as e:
        file_type = "csv" if is_csv else "excel"
        raise FileParsingError(file_type, e)

# --- КЛАСС-ФАСАД ДЛЯ РОУТЕРА ---
class OCRService:
    @retry()
    @log_async_time
    async def extract_text(self, file_or_bytes: UploadFile | bytes, content_type: str) -> str:
        """
        Извлечение текста из файла.

        Args:
            file_or_bytes: Файл или бинарные данные
            content_type: MIME-тип файла

        Returns:
            Извлеченный текст

        Raises:
            UnsupportedFileFormatError: Если формат не поддерживается
            FileParsingError: Если парсинг завершился ошибкой
        """
        try:
            # if UploadFile passed - read bytes inside service
            if hasattr(file_or_bytes, "read"):
                # Важно для @retry: сбрасываем указатель, если это повторная попытка
                if hasattr(file_or_bytes, "seek"):
                    await file_or_bytes.seek(0)
                file_bytes = await file_or_bytes.read()
            else:
                file_bytes = file_or_bytes

            match content_type:
                case "application/pdf":
                    return await run_in_threadpool(parse_pdf, file_bytes)
                case "image/png" | "image/webp" | "image/jpeg":
                    return await run_in_threadpool(parse_image, file_bytes)
                case "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" | "application/vnd.ms-excel":
                    return await run_in_threadpool(parse_table, file_bytes, is_csv = False)
                case "text/csv":
                    return await run_in_threadpool(parse_table, file_bytes, is_csv = True)
                case _:
                    raise UnsupportedFileFormatError(content_type)
        except (FileParsingError, UnsupportedFileFormatError):
            raise
        except Exception as e:
            logger.error(
                f"Неожиданная ошибка при извлечении текста: {str(e)}",
                exc_info=True,
            )
            raise OCRProcessingError(f"Неожиданная ошибка при обработке файла: {str(e)}")

ocr_service = OCRService()


