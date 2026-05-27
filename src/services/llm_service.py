import logging
from google import genai
from google.genai import types

from src.config import settings
from src.schemas.analysis import MedicalAnalysisResult
from src.exceptions import GeminiAPIError, GeminiParsingError


logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key) # Кей сам подтягивается из енва, но на всякий стоит указать
        self.model_name = "gemini-2.5-flash" # Бесплатно, большой контекст, нормально делается json

    async def analyze_text(self, raw_text: str) -> MedicalAnalysisResult:
        """
        Интерпретация от Gemini
        :param raw_text: Грязный текст от OCR
        :return: MedicalAnalysisResult
        """

        logger.info("Начало отправки запроса в Gemini. Длина сырого текста: %d.", len(raw_text))

        system_instruction = (
            "Ты — профессиональный медицинский ассистент. Твоя задача — проанализировать "
            "грязный текст, полученный после распознавания (OCR) бланка анализов крови.\n"
            "Изучи текст, найди имя пациента, дату, лабораторию и все медицинские показатели.\n"
            "Заполни структуру данных в строгом соответствии с запрашиваемой схемой JSON.\n"
            "Если какие-то данные (например, имя или дата) отсутствуют в тексте, оставь их null.\n"
            "Важно: не придумывай показатели, бери только то, что есть в тексте."
        )

        # Конфиг запроса, температуру пониже чтобы не воображал
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=MedicalAnalysisResult,
        )

        try:
            # .aio асинхронный интерфейс google-genai
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=f"Вот текст бланка анализов:\n\n{raw_text}",
                config=config
            )
            # Думаю стоит пояснить, если мы сразу пойдём отдавать на валидацию response.text
            # а не прокладку в виде response_text, то тогда линтер ругается что тип может быть
            # str | None, так что я гарантированно отдаю str на валидацию и всё спокойно, не спеша, не дыша и тд
            response_text = response.text


            if not response_text:
                logger.warning("Gemini вернула пустой ответ или контент заблокирован.")
                raise GeminiParsingError(
                    message="Не удалось извлечь данные из документа.",
                    detail={
                        "reason": "empty_response",
                        "model": self.model_name,
                        "safety_ratings": str(response.prompt_feedback) if hasattr(response, "prompt_feedback") else "unknown",
                    }
                )

            structured_data = MedicalAnalysisResult.model_validate_json(response_text)
            logger.info(
                "Документ успешно распарсен ИИ. Извлечено показателей: %d",
                len(structured_data.indicators),
            )

            return structured_data

        except (GeminiAPIError, GeminiParsingError) as e:
            raise e # хандлер сам словит

        except Exception as e:
            logger.error(
                "Сервер Google не отвечает",
                exc_info=True,
            )
            raise GeminiAPIError(
                message="Сервис ИИ временно недоступен.",
                detail={"raw_error": str(e)},
            )



