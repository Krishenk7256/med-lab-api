from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database import engine, Base
from src.routers.lab_router import router as lab_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(lab_router)


@app.get("/")
def read_root():
    return {"status": "alive", "service": "med-lab-api"}