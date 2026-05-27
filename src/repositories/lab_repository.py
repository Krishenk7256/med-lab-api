from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from fastapi import Depends

from src.models.lab import LabReport
from src.exceptions import DatabaseError
from src.database import get_db


logger = logging.getLogger(__name__)


class LabRepository:
    """
    Репозиторий для LabReport
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Соединение с БД
        :param db: AsyncSession
        """
        self.db = db

    # CREATE
    async def create(self,
                     patient_name: Optional[str],
                     raw_text: str,
                     interpreted_result: str,
                     ) -> LabReport:
        """
        Создать новый отчёт в БД
        :param patient_name: Имя пациента
        :param raw_text: Распознанный текст
        :param interpreted_result: Интерпретация (опциально)
        :return: Созданный LabReport объект
        :raises: DatabaseError: Если ошибка при создании
        """
        try:
            report = LabReport(
                patient_name=patient_name or "Неизвестный пациент",
                raw_text=raw_text,
                interpreted_result=interpreted_result,
            )

            self.db.add(report)

            await self.db.commit()

            await self.db.refresh(report)

            logger.info(f"Создан отчёт с ID {report.id}")
            return report

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка при создании отчёта: {str(e)}", exc_info=True)
            raise DatabaseError(f"Ошибка при создании отчёта: {str(e)}")

    # READ
    async def get_by_id(self, report_id: int) -> Optional[LabReport]:
        """
        Получить отчёт по ID
        :param report_id: ID отчёта
        :return: LabReport или None если не найден
        """
        try:
            # SELECT * FROM lab_reports WHERE id = report_id
            result = await self.db.execute(
                select(LabReport).where(LabReport.id == report_id)
            )
            report = result.scalars().first()

            if report:
                logger.debug(f"Найден отчёт с ID {report.id}")
            else:
                logger.debug(f"Отчёт с ID {report_id} не найден")

            return report

        except Exception as e:
            logger.error(f"Ошибка при получении отчёта {report_id}", exc_info=True)
            raise DatabaseError(f"Ошибка при получении отчёта: {str(e)}")

    async def get_all(self,
                      skip: int = 0,
                      limit: int = 10,
                      ) -> List[LabReport]:
        """
        Получить все отчёты с пагинацией
        :param skip: Сколько пропустить (для пагинации)
        :param limit: Сколько вернуть
        :return: Список отчётов
        """
        try:
            # SELECT * FROM lab_reports
            # ORDER BY created_at DESC
            # LIMIT limit OFFSET skip
            result = await self.db.execute(
                select(LabReport)
                .order_by(desc(LabReport.created_at))
                .offset(skip)
                .limit(limit)
            )
            reports = result.scalars().all()
            logger.debug(f"Получено {len(reports)} отчётов")
            return list(reports)

        except Exception as e:
            logger.error(f"Ошибка при получении отчётов: {str(e)}", exc_info=True)
            raise DatabaseError(f"Ошибка при получении отчётов: {str(e)}")

    async def search(self,
                     patient_name: str,
                     skip: int = 0,
                     limit: int = 10,
                     ) -> List[LabReport]:
        """
        Поиск отчётов по имени пациента
        :param patient_name: Часть имени для поиска
        :param skip: Сколько пропустить
        :param limit: Сколько вернуть
        :return: Найденные отчёты
        """
        try:
            # SELECT * FROM lab_reports
            # WHERE patient_name LIKE '%patient_name'
            # ORDER BY created_at DESC
            result = await self.db.execute(
                select(LabReport)
                .where(LabReport.patient_name.ilike(f"%{patient_name}%"))
                .order_by(desc(LabReport.created_at))
                .offset(skip)
                .limit(limit)
            )
            reports = result.scalars().all()
            logger.info(f"Найдено {len(reports)} отчётов по запросу: '{patient_name}'")
            return list(reports)

        except Exception as e:
            logger.error(f"Ошибка при поиске отчётов: {str(e)}", exc_info=True)
            raise DatabaseError(f"Ошибка при поиске отчётов: {str(e)}")

    # UPDATE
    async def update(self,
                     report_id: int,
                     interpreted_result: str,
                     ) -> Optional[LabReport]:
        """
        Обновить интерпретацию отчёта
        :param report_id: ID отчёта
        :param interpreted_result: Новая интерпретация
        :return: Обновлённый отчёт или None если не найден
        """
        try:
            report = await self.get_by_id(report_id)
            if not report:
                logger.warning(f"Невозможно обновить: отчёт {report_id} не найден")
                return None

            report.interpreted_result = interpreted_result

            await self.db.commit()

            await self.db.refresh(report)

            logger.info(f"Обновлён отчёт {report_id}")
            return report

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка при обновлении отчёта {report_id}", exc_info=True)
            raise DatabaseError(f"Ошибка при обновлении отчёта: {str(e)}")

    # DELETE
    async def delete(self, report_id: int) -> bool:
        """
        Удалить отчёт
        :param report_id: ID отчёта
        :return: True - успешно / False - неуспешно
        """
        try:
            report = await self.get_by_id(report_id)
            if not report:
                logger.warning(f"Невозможно удалить: отчёт {report_id} не найден")
                return False

            await self.db.delete(report)

            await self.db.commit()

            logger.info(f"Удалён отчёт {report_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка при удалении отчёта {report_id}", exc_info=True)
            raise DatabaseError(f"Ошибка при удалении отчёта: {str(e)}")


async def get_lab_repository(db: AsyncSession = Depends(get_db)) -> LabRepository:
    """
    Dependency функция дли роутеров
    :param db: AsyncSession = Depends(get_db)
    :return: LabRepository(db)
    """
    return LabRepository(db)