from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
import logging


from src.repositories.lab_repository import get_lab_repository, LabRepository
from src.exceptions import ValidationError, FileSizeError, LabReportNotFoundError
from src.schemas.lab import LabReportResponse, LabReportListResponse
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


# CREATE
@router.post(
    "upload",
    response_model=LabReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_analysis(
        patient_name: str = Form(...),
        file: UploadFile = File(...),
        repo: LabRepository = Depends(get_lab_repository),
):
    """
    Загрузка медицинского анализа для OCR
    :param patient_name: Имя пациента
    :param file: Файл анализа (PDF, image, table)
    """
    try:
        patient_name = validate_patient_name(patient_name)
        file = await validate_file(file)

        logger.info(f"Обработка файла пациента: {patient_name}")

        file_bytes = await file.read()
        if not file_bytes:
            raise ValidationError("Файл пуст", detail={"field": "file"})

        extracted_text = ocr_service.extract_text(file_bytes, file.content_type)

        new_report = await repo.create(
            patient_name=patient_name,
            raw_text=extracted_text,
            interpreted_result="В процессе..."
        )

        logger.info(f"Отчёт создан: ID={new_report.id}")
        return new_report

    except Exception as e:
        logger.error(f"Ошибка при загрузке анализа: {str(e)}", exc_info=True)
        raise


# Read single
@router.get("/{report_id}", response_model=LabReportResponse)
async def get_report(
        report_id: int,
        repo: LabRepository = Depends(get_lab_repository),
):
    """
    Получить отчёт по ID
    :param report_id: ID отчёта
    """
    report = await repo.get_by_id(report_id)

    if not report:
        raise LabReportNotFoundError(report_id)

    return report

# Read all
@router.get("/", response_model=LabReportListResponse)
async def list_reports(
        skip: int = Query(0, ge=0, desciption="Количество пропущенных отчётов"),
        limit: int = Query(10, ge=1, le=100, description="Количество нужных отчётов"),
        search: str = Query(None, description="Поиск по имени пациента"),
        repo: LabRepository = Depends(get_lab_repository),
):
    """
    Получить список всех отчётов с пагинацией и поиском
    :param skip: Скипнуть N отчётов
    :param limit: Вернуть N отчётов
    :param search: Поиск по имени пациента (Optional)
    """
    try:
        if search:
            reports = await repo.search(search, skip=skip, limit=limit)
        else:
            reports = await repo.get_all(skip=skip, limit=limit)

        return {
            "items": reports,
            "skip": skip,
            "limit": limit,
            "total": len(reports),
        }

    except Exception as e:
        logger.error(f"Ошибка создания списка отчётов: {str(e)}", exc_info=True)
        raise

# Update
@router.put("/{report_id}", response_model=LabReportResponse)
async def update_report(
        report_id: int,
        interpreted_result: str = Form(...),
        repo: LabRepository = Depends(get_lab_repository),
):
    """
    Обновить интерпретацию отчёта
    :param report_id: ID отчёта
    :param interpreted_result: Новая интерпретация
    """
    try:
        report = await repo.update(report_id, interpreted_result)

        if not report:
            raise LabReportNotFoundError(report_id)

        logger.info(f"Отчёт {report_id} обновлён")
        return report

    except Exception as e:
        logger.error(f"Ошибка обновления отчёта: {str(e)}", exc_info=True)
        raise

# Delete
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
        report_id: int,
        repo: LabRepository = Depends(get_lab_repository),
):
    """
    Удалить отчёт
    :param report_id: ID отчёта
    """
    try:
        success = await repo.delete(report_id)

        if not success:
            raise LabReportNotFoundError(report_id)

        logger.info(f"Отчёт {report_id} удалён")

    except Exception as e:
        logger.error(f"Ошибка при удалении отчёта: {str(e)}", exc_info=True)
        raise
