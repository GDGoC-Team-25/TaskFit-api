from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.evaluation import Evaluation
from src.models.database.submission import Submission
from src.models.database.task import Task
from src.models.database.user import User


async def get_profile(db: AsyncSession, user_id: int) -> dict | None:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None

    # 총 풀이 수 (submitted + evaluated)
    total_solved = (
        await db.execute(
            select(func.count(Submission.id)).where(
                Submission.user_id == user_id,
                Submission.status != "draft",
            )
        )
    ).scalar() or 0

    # 평균 점수
    sub_ids_stmt = select(Submission.id).where(
        Submission.user_id == user_id,
        Submission.status != "draft",
    )
    avg_score_result = await db.execute(
        select(func.avg(Evaluation.total_score)).where(
            Evaluation.submission_id.in_(sub_ids_stmt)
        )
    )
    avg_score = avg_score_result.scalar() or 0.0

    # 최근 평가 (최대 5개)
    recent_evals_stmt = (
        select(Evaluation)
        .where(Evaluation.submission_id.in_(sub_ids_stmt))
        .order_by(Evaluation.created_at.desc())
        .limit(5)
    )
    recent_evals = list((await db.execute(recent_evals_stmt)).scalars().all())

    recent_submissions = []
    for ev in recent_evals:
        submission = (
            await db.execute(select(Submission).where(Submission.id == ev.submission_id))
        ).scalar_one_or_none()
        task = None
        if submission:
            task = (
                await db.execute(select(Task).where(Task.id == submission.task_id))
            ).scalar_one_or_none()
        recent_submissions.append({
            "id": ev.id,
            "task_title": task.title if task else "알 수 없음",
            "total_score": ev.total_score,
            "created_at": ev.created_at,
        })

    return {
        "user": user,
        "stats": {
            "total_solved": total_solved,
            "avg_score": round(float(avg_score), 1),
            "rank_percentile": None,
        },
        "recent_submissions": recent_submissions,
    }


async def update_profile(
    db: AsyncSession,
    user_id: int,
    *,
    name: str | None = None,
    bio: str | None = None,
) -> User | None:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None

    if name is not None:
        user.name = name
    if bio is not None:
        user.bio = bio

    await db.commit()
    await db.refresh(user)
    return user
