from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.submission import Submission


async def create_submission(
    db: AsyncSession,
    *,
    user_id: int,
    task_id: int,
    content: str,
    is_draft: bool = False,
    time_spent_seconds: int | None = None,
) -> Submission:
    status = "draft" if is_draft else "submitted"
    submission = Submission(
        user_id=user_id,
        task_id=task_id,
        content=content,
        is_draft=is_draft,
        status=status,
        time_spent_seconds=time_spent_seconds,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def update_submission(
    db: AsyncSession,
    submission: Submission,
    *,
    content: str,
    is_draft: bool = False,
    time_spent_seconds: int | None = None,
) -> Submission:
    submission.content = content
    submission.is_draft = is_draft
    submission.status = "draft" if is_draft else "submitted"
    if time_spent_seconds is not None:
        submission.time_spent_seconds = time_spent_seconds
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_submission(db: AsyncSession, submission_id: int) -> Submission | None:
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    return result.scalar_one_or_none()


async def get_user_submission_for_task(
    db: AsyncSession, user_id: int, task_id: int
) -> Submission | None:
    result = await db.execute(
        select(Submission).where(
            Submission.user_id == user_id, Submission.task_id == task_id
        )
    )
    return result.scalar_one_or_none()
