import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context
from app.core.config import settings
from app.core.database import Base, create_database_engine

config = context.config
fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", settings.async_database_url)

target_metadata = Base.metadata


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_database_engine(poolclass=pool.NullPool, use_pool=False)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


asyncio.run(run_migrations_online())
