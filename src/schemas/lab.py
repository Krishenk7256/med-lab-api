from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LabReportResponse(BaseModel):
    id: int
    patient_name: str
    interpreted_result: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True