from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    google_id: str,
    email: str,
    name: str,
    profile_image: str | None = None,
) -> User:
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        profile_image=profile_image,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
