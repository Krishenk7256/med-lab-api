from pydantic import BaseModel, Field
from typing import List, Optional

class BloodIndicator(BaseModel):
    name: str = Field(
        description="Название медицинского показателя. Например: гемоглобин, эритроциты, нейтрофилы"
    )
    value: float = Field(
        description="Числовое значение показателя"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Единица измерения показания"
    )
    reference_range: Optional[str]= Field(
        default=None,
        description="Референсные значения из бланка"
    )

class MedicalAnalysisResult(BaseModel):
    patient_name: Optional[str] = Field(
        default=None,
        description="Имя пациента, если есть в бланке"
    )
    analysis_date: Optional[str] = Field(
        default=None,
        description="Дата сдачи анализа в формате ДД.ММ.ГГГГ"
    )
    laboratory: Optional[str] = Field(
        default=None,
        description="Название лаборатории, которая проводила анализ"
    )
    indicators: List[BloodIndicator] = Field(
        description="Список всех извлечённых медицинских показателей"
    )