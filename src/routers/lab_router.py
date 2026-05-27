from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
import logging


from src.repositories.lab_repository import get_lab_repository, LabRepository
from src.exceptions import LabReportNotFoundError
from src.schemas.lab import LabReportResponse, LabReportListResponse
from src.services.llm_service import GeminiService
from src.services.ocr_service import ocr_service
from src.utils.validators import validate_file


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/labs", tags=["Лабораторные анализы"])


# CREATE
@router.post(
    "/upload",
    response_model=LabReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_analysis(
        patient_name: str = Form(...),
        file: UploadFile = File(...),
        repo: LabRepository = Depends(get_lab_repository),
        llm_service: GeminiService = Depends()
):
    """
    Загрузка анализа -> OCR -> Gemini -> БД
    :param patient_name: Имя пациента
    :param file: Анализ
    :param repo: Метод Create
    :param llm_service: Работа с GeminiService
    :return: Готовый отчёт из БД
    """
    try:

        await validate_file(file)

        logger.info(f"Обработка файла пациента: {patient_name}")
        raw_text = await ocr_service.extract_text(file, file.content_type)

        structured_data = await llm_service.analyze_text(raw_text)

        new_report = await repo.create(
            patient_name=structured_data.patient_name,
            raw_text=raw_text,
            interpreted_result=structured_data.model_dump_json()
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
    :param repo: Метод Get
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
    :param repo: Метод Create
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
    :param repo: Метод Put
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
    :param repo: Метод Delete
    """
    try:
        success = await repo.delete(report_id)

        if not success:
            raise LabReportNotFoundError(report_id)

        logger.info(f"Отчёт {report_id} удалён")

    except Exception as e:
        logger.error(f"Ошибка при удалении отчёта: {str(e)}", exc_info=True)
        raise
