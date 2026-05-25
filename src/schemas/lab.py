from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LabReportResponse(BaseModel):
    """Response с одним отчётом"""
    id: int = Field(..., description="ID отчёта")
    patient_name: str = Field(..., description="Имя пациента")
    interpreted_result: Optional[str] = Field(None, description="")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LabReportListResponse(BaseModel):
    """Response для списка отчётов"""
    items: List[LabReportResponse]
    skip: int
    limit: int
    total: int

    class Config:
        from_attributes = True