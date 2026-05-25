from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from src.database import engine, Base
from src.routers.lab_router import router as lab_router
from src.exceptions import APIException
from src.schemas.error import ErrorResponse


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Med Lab API",
    description="Сервис распознования медицинских анализов",
    version="1.0.0",
    lifespan=lifespan)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Обработчик для всех APIException"""
    error_response = ErrorResponse(
        error_code=exc.status_code,
        message=exc.message,
        status_code=exc.status_code,
        detail=exc.detail if exc.detail else None,
    )
    logger.warning(f"API Exception: {exc.error_code} | {exc.message} | {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Непредвиденная ошибка: {str(exc)} | {request.url}", exc_info=True)
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="Внутрення ошибка сервера",
        status_code=500,
        detail=None,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(exclude_none=True),
    )
app.include_router(lab_router)


@app.get("/")
def read_root():
    return {"status": "alive", "service": "med-lab-api"}