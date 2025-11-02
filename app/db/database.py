from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from . import models 
from config import DATABASE_URL
from typing import AsyncGenerator
import logging 

class Base(DeclarativeBase):
    pass

if DATABASE_URL and not DATABASE_URL.startswith("postgresql+asyncpg"):
    MODIFIED_DATABASE_URL = DATABASE_URL.replace("postgresql", "postgresql+asyncpg", 1)
    logging.info("DATABASE_URL модифицирован для использования asyncpg.")
else:
    MODIFIED_DATABASE_URL = DATABASE_URL

engine = create_async_engine(MODIFIED_DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info("База данных инициализирована и таблицы созданы.")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db_session() -> AsyncSession:
    """Простой асинхронный метод для получения сессии."""
    return AsyncSessionLocal()
