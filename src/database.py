from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://med_user:med_password@db:5432/med_db"

engine = create_async_engine(DATABASE_URL, echo=True)


async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session(bind=engine) as session:
        yield session