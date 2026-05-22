from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Float, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True)

    patient_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=False)

    created_at: Mapped[str] = mapped_column(
        String(50),
        default="COMPLETED")

    results: Mapped[List["BiomarkerResult"]] = relationship(
        back_populates="report", cascade="all, delete-orphan")


class BiomarkerResult(Base):
    __tablename__ = "biomarker_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    report_id: Mapped[int] = mapped_column(ForeignKey("lab_reports.id",
                                                      ondelete="CASCADE"))
