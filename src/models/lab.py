from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column


from src.database import Base

class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    interpreted_result: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
