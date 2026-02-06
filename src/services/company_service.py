from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.company import Company


async def search_companies(
    db: AsyncSession, q: str | None = None, limit: int = 20
) -> list[Company]:
    stmt = select(Company)
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Company.name).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
