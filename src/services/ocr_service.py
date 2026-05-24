import io
import pandas as pd
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
from fastapi.concurrency import run_in_threadpool

from src.utils.decorators import retry, log_async_time

# Поддержка пдф, изображений, таблиц. Это всё синхронно, но заворачивается в тредпул
#@log_sync_time
def parse_pdf(file_bytes: bytes) -> str:
    images = convert_from_bytes(file_bytes)
    full_text = []
    for image in images:
        text = pytesseract.image_to_string(image, lang="rus+eng")
        full_text.append(text)
    return "".join(full_text)

#@log_sync_time
def parse_image(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image, lang="rus+eng")
    return text.strip()

#@log_sync_time
def parse_table(file_bytes: bytes, is_csv = False) -> str:
    buffer = io.BytesIO(file_bytes)
    df = pd.read_csv(buffer) if is_csv else pd.read_excel(buffer)
    return df.to_string(index = False)

# --- КЛАСС-ФАСАД ДЛЯ РОУТЕРА ---
class OCRService:
    @staticmethod
    @retry()
    @log_async_time
    async def extract_text(file_bytes: bytes, content_type: str) -> str:
        try:
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
                    return f"[Ошибка]: Неподдерживаемый формат файла: {content_type}"
        except Exception as e:
            return f"[Ошибка обработки файла {content_type}]: {str(e)}"

ocr_service = OCRService()


