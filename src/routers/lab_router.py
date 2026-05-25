from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_db
from src.exceptions import ValidationError, FileSizeError, LabReportNotFoundError
from src.models.lab import LabReport
from src.schemas.lab import LabReportResponse
from src.services.ocr_service import ocr_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/labs", tags=["Лабораторные анализы"])

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

def validate_patient_name(name: str) -> str:
    """Валидация имени пациента"""
    if not name or len(name.strip()) == 0:
        raise ValidationError(
            "Имя пациента не может быть пустым",
            detail={"field": "patient_name"},
        )
    if len(name) > 100:
        raise ValidationError(
            "Имя пациента не может быть длиннее 100 символов",
            detail={"field": "patient_name", "max_length": 100},
        )
    return name.strip()

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


@router.post(
    "/upload",
    response_model=LabReportResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Ошибка валидации или парсинга файла"},
        413: {"description": "Файл слишком большой"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def upload_analysis(
    patient_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Загрузить медицинский анализ для распознования

    - **patient_name**: ФИО пациента (макс 100 символов)
    - **file**: Файл анализа (PDF, изображение или таблица)
    """
    try:
        patient_name = validate_patient_name(patient_name)
        file = await validate_file(file)
        logger.info(f"Обработка файла: {file.filename} для пациента: {patient_name}")

        # Читаем файл
        file_bytes = await file.read()
        if not file_bytes:
            raise ValidationError("Файл пустой", detail={"field": "file"})

        # Читаем молитвы чтобы текст извлёкся (или выплюнет исключение)
        extracted_text = await ocr_service.extract_text(file_bytes, file.content_type)

        # Добавляем сырой текст в бд
        new_report = LabReport(
            patient_name=patient_name,
            raw_text=extracted_text,
            interpreted_result="Анализ успешно распознан. Интерпретация в процессе..."
        )

        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)

        logger.info(f"Отчёт создан: ID: {new_report.id}")
        return new_report

    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при загрузке анализов: {str(e)}", exc_info=True)
        raise # Само поймёт

@router.get("/report_id", response_model=LabReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Получить отчёт по ID"""
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(LabReport).where(LabReport.id == report_id)
        )
        report = result.scalars().first()

        if not report:
            raise LabReportNotFoundError(report_id)

        return report
    except Exception as e:
        logger.error(f"Ошибка при получении отчёта: {report_id}: {str(e)}", exc_info=True)
        raise




