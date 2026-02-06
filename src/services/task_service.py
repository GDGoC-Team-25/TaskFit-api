from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.task import Task


async def get_tasks(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    company_id: int | None = None,
    job_role_id: int | None = None,
    category: str | None = None,
    difficulty: str | None = None,
) -> tuple[list[Task], int]:
    stmt = select(Task)
    count_stmt = select(func.count(Task.id))

    if company_id:
        stmt = stmt.where(Task.company_id == company_id)
        count_stmt = count_stmt.where(Task.company_id == company_id)
    if job_role_id:
        stmt = stmt.where(Task.job_role_id == job_role_id)
        count_stmt = count_stmt.where(Task.job_role_id == job_role_id)
    if category:
        stmt = stmt.where(Task.category == category)
        count_stmt = count_stmt.where(Task.category == category)
    if difficulty:
        stmt = stmt.where(Task.difficulty == difficulty)
        count_stmt = count_stmt.where(Task.difficulty == difficulty)

    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def get_task_detail(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def create_tasks_batch(db: AsyncSession, tasks_data: list[dict]) -> list[Task]:
    tasks = [Task(**data) for data in tasks_data]
    db.add_all(tasks)
    await db.commit()
    for task in tasks:
        await db.refresh(task)
    return tasks
