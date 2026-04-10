import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.core.config import settings
from app.setup.seed_users import seed_users
from app.setup.seed_hardware import seed_hardware


async def already_seeded(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT COUNT(*) FROM hardware"))
    return result.scalar() > 0


async def main():
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"ssl": "require"},
        poolclass=NullPool,
    )
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        if await already_seeded(session):
            print("Already seeded — skipping.")
            await engine.dispose()
            return

        print("Seeding stackgear-ai...\n")

        await seed_users(session)
        await seed_hardware(session)

        await session.commit()
        print(f"\n✓ Seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())