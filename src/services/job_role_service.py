from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.job_role import JobRole


async def get_categories(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(distinct(JobRole.category)).order_by(JobRole.category)
    )
    return list(result.scalars().all())


async def search_job_roles(
    db: AsyncSession,
    category: str | None = None,
    q: str | None = None,
) -> list[JobRole]:
    stmt = select(JobRole)
    if category:
        stmt = stmt.where(JobRole.category == category)
    if q:
        stmt = stmt.where(JobRole.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(JobRole.category, JobRole.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())
