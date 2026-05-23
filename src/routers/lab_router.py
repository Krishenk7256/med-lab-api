from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.lab import LabReport
from src.schemas.lab import LabReportResponse
from src.services.ocr_service import ocr_service

router = APIRouter(prefix="/labs", tags=["Лабораторные анализы"])

@router.post("/upload", response_model=LabReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_analysis(
    patient_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Читаем бинарник в память
    file_bytes = await file.read()

    extracted_text = await ocr_service.extract_text(file_bytes, file.content_type)

    if extracted_text.startswith("[Ошибка]"):
        raise HTTPException(status_code=400, detail=extracted_text)

    # Добавляем сырой текст в бд
    new_report = LabReport(
        patient_name=patient_name,
        raw_text=extracted_text,
        interpreted_result="Анализ успешно распознан. Интерпретация в процессе..."
    )

    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    return new_report



