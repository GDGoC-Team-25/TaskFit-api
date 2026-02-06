from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.evaluation import Evaluation
from src.models.database.user_competency import UserCompetency


async def create_evaluation(
    db: AsyncSession,
    *,
    submission_id: int,
    thread_id: int,
    total_score: int,
    score_label: str,
    scores_detail: list[dict],
    ai_summary: str,
    analysis_points: dict,
    feedback: str | None = None,
) -> Evaluation:
    evaluation = Evaluation(
        submission_id=submission_id,
        thread_id=thread_id,
        total_score=total_score,
        score_label=score_label,
        scores_detail=scores_detail,
        ai_summary=ai_summary,
        analysis_points=analysis_points,
        feedback=feedback,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


async def get_evaluation_detail(
    db: AsyncSession, evaluation_id: int
) -> Evaluation | None:
    result = await db.execute(
        select(Evaluation).where(Evaluation.id == evaluation_id)
    )
    return result.scalar_one_or_none()


async def get_evaluation_by_submission_id(
    db: AsyncSession, submission_id: int
) -> Evaluation | None:
    result = await db.execute(
        select(Evaluation).where(Evaluation.submission_id == submission_id)
    )
    return result.scalar_one_or_none()


async def update_user_competency(
    db: AsyncSession,
    *,
    user_id: int,
    company_id: int,
    job_role_id: int,
    new_score: int,
    weak_tags: list[str] | None = None,
) -> UserCompetency:
    result = await db.execute(
        select(UserCompetency).where(
            UserCompetency.user_id == user_id,
            UserCompetency.company_id == company_id,
            UserCompetency.job_role_id == job_role_id,
        )
    )
    competency = result.scalar_one_or_none()

    if competency:
        total = competency.avg_score * competency.attempt_count + new_score
        competency.attempt_count += 1
        competency.avg_score = total / competency.attempt_count
        if weak_tags is not None:
            competency.weak_tags = weak_tags
    else:
        competency = UserCompetency(
            user_id=user_id,
            company_id=company_id,
            job_role_id=job_role_id,
            avg_score=float(new_score),
            attempt_count=1,
            weak_tags=weak_tags,
        )
        db.add(competency)

    await db.commit()
    await db.refresh(competency)
    return competency
