from pdf2image import convert_from_bytes
import pytesseract
from fastapi.concurrency import run_in_threadpool


class OCRService:
    @staticmethod
    def _sync_extract(file_bytes: bytes) -> str:
        images = convert_from_bytes(file_bytes)
        full_text = []
        for image in images:
            text = pytesseract.image_to_string(image)
            full_text.append(text)
        return "".join(full_text)
    @staticmethod
    async def extract_text_from_pdf(file_bytes: bytes) -> str:
        try:
            text = await run_in_threadpool(OCRService._sync_extract, file_bytes)
            return text
        except Exception as e:
            return f"[Ошибка OCR обработки]: {str(e)}"

ocr_service = OCRService()