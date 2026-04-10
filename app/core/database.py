from urllib.parse import urlsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def create_database_engine(*, echo: bool = False, use_pool: bool = True, **kwargs):
    engine_kwargs = {
        "echo": echo,
        "connect_args": settings.asyncpg_connect_args,
    }

    if use_pool:
        engine_kwargs.update(
            {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
            }
        )

    engine_kwargs.update(kwargs)
    return create_async_engine(settings.async_database_url, **engine_kwargs)


def database_endpoint_summary() -> str:
    parts = urlsplit(settings.async_database_url)
    host = parts.hostname or "<missing-host>"
    port = parts.port or 5432
    database = parts.path.lstrip("/") or "<missing-database>"
    return f"{host}:{port}/{database}"


engine = create_database_engine(echo=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
