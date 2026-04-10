import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.models.user import User


async def seed_users(session: AsyncSession) -> None:
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@stackgear.com",
        username="admin",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )
    session.add(admin)
    await session.flush()
    print(f"  + Admin: {admin.email} / admin123")