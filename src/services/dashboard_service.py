from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.company import Company
from src.models.database.evaluation import Evaluation
from src.models.database.job_role import JobRole
from src.models.database.submission import Submission
from src.models.database.task import Task
from src.models.database.user_competency import UserCompetency


async def get_dashboard_summary(db: AsyncSession, user_id: int) -> dict:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # 주간 제출 (submitted/evaluated 상태)
    weekly_subs_stmt = select(Submission).where(
        Submission.user_id == user_id,
        Submission.status != "draft",
        Submission.created_at >= week_ago,
    )
    weekly_subs = list((await db.execute(weekly_subs_stmt)).scalars().all())
    weekly_sub_ids = [s.id for s in weekly_subs]

    # 주간 평가 점수
    weekly_scores = []
    weekly_time_total = 0
    if weekly_sub_ids:
        evals_stmt = select(Evaluation).where(
            Evaluation.submission_id.in_(weekly_sub_ids)
        )
        weekly_evals = list((await db.execute(evals_stmt)).scalars().all())
        weekly_scores = [e.total_score for e in weekly_evals]

    for s in weekly_subs:
        if s.time_spent_seconds:
            weekly_time_total += s.time_spent_seconds

    problems_solved = len(weekly_subs)
    score_percentage = (sum(weekly_scores) / len(weekly_scores)) if weekly_scores else 0.0
    avg_time_minutes = (weekly_time_total / problems_solved / 60) if problems_solved else 0.0

    # 약점 태그 수
    competencies_stmt = select(UserCompetency).where(
        UserCompetency.user_id == user_id
    )
    competencies = list((await db.execute(competencies_stmt)).scalars().all())
    weak_tags_set: set[str] = set()
    for c in competencies:
        if c.weak_tags:
            weak_tags_set.update(c.weak_tags)

    weekly_summary = {
        "score_percentage": round(score_percentage, 1),
        "problems_solved": problems_solved,
        "avg_time_minutes": round(avg_time_minutes, 1),
        "weak_tag_count": len(weak_tags_set),
    }

    # AI 인사이트 (정적 텍스트)
    ai_insight = {
        "improvements": "꾸준한 과제 풀이를 통해 실력이 향상되고 있습니다."
        if problems_solved > 0
        else "이번 주 과제를 시작해보세요!",
        "weak_areas": ", ".join(list(weak_tags_set)[:3]) if weak_tags_set else "아직 데이터가 부족합니다.",
    }

    # 최근 제출 목록 (최대 10개)
    recent_stmt = (
        select(Submission)
        .where(Submission.user_id == user_id, Submission.status != "draft")
        .order_by(Submission.created_at.desc())
        .limit(10)
    )
    recent_subs = list((await db.execute(recent_stmt)).scalars().all())

    recent_submissions = []
    for sub in recent_subs:
        task = (await db.execute(select(Task).where(Task.id == sub.task_id))).scalar_one_or_none()
        eval_row = (
            await db.execute(select(Evaluation).where(Evaluation.submission_id == sub.id))
        ).scalar_one_or_none()

        recent_submissions.append({
            "id": sub.id,
            "task_title": task.title if task else "알 수 없음",
            "category": task.category if task else "",
            "total_score": eval_row.total_score if eval_row else None,
            "is_correct": (eval_row.total_score >= 60) if eval_row else None,
            "time_spent_seconds": sub.time_spent_seconds,
            "created_at": sub.created_at,
        })

    # 역량 요약
    competency_summaries = []
    for c in competencies:
        company = (await db.execute(select(Company).where(Company.id == c.company_id))).scalar_one_or_none()
        job_role = (await db.execute(select(JobRole).where(JobRole.id == c.job_role_id))).scalar_one_or_none()
        competency_summaries.append({
            "company_name": company.name if company else "알 수 없음",
            "job_role_name": job_role.name if job_role else "알 수 없음",
            "avg_score": round(c.avg_score, 1),
            "attempt_count": c.attempt_count,
            "weak_tags": c.weak_tags,
        })

    return {
        "weekly_summary": weekly_summary,
        "ai_insight": ai_insight,
        "recent_submissions": recent_submissions,
        "competencies": competency_summaries,
    }
