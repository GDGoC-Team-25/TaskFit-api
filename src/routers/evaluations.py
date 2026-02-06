from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import success_response
from src.models.schemas.company import CompanyBrief
from src.models.schemas.evaluation import (
    AnalysisPoints,
    EvaluationDetailResponse,
    ScoreDetail,
    SubmissionInEvaluation,
    TaskInEvaluation,
    ThreadInEvaluation,
)
from src.models.schemas.job_role import JobRoleBrief
from src.services import (
    company_service,
    evaluation_service,
    submission_service,
    task_service,
    thread_service,
)

router = APIRouter(prefix="/evaluations", tags=["평가"])


@router.get("/{evaluation_id}", response_model=dict)
async def get_evaluation_detail(
    evaluation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """평가 상세를 조회한다."""
    evaluation = await evaluation_service.get_evaluation_detail(db, evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVALUATION_NOT_FOUND", "message": "평가를 찾을 수 없습니다"},
        )

    submission = await submission_service.get_submission(db, evaluation.submission_id)
    if not submission or submission.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "권한이 없습니다"},
        )

    task = await task_service.get_task_detail(db, submission.task_id)

    # 기업, 직무 조회
    company_brief = CompanyBrief(id=0, name="알 수 없음")
    job_role_brief = JobRoleBrief(id=0, name="알 수 없음")
    if task:
        companies = await company_service.search_companies(db)
        company = next((c for c in companies if c.id == task.company_id), None)
        if company:
            company_brief = CompanyBrief.model_validate(company)

        from src.services import job_role_service

        roles = await job_role_service.search_job_roles(db)
        job_role = next((r for r in roles if r.id == task.job_role_id), None)
        if job_role:
            job_role_brief = JobRoleBrief.model_validate(job_role)

    thread = await thread_service.get_thread_detail(db, evaluation.thread_id)

    response = EvaluationDetailResponse(
        id=evaluation.id,
        total_score=evaluation.total_score,
        score_label=evaluation.score_label,
        scores_detail=[ScoreDetail(**s) for s in evaluation.scores_detail],
        ai_summary=evaluation.ai_summary,
        analysis_points=AnalysisPoints(**evaluation.analysis_points),
        feedback=evaluation.feedback,
        submission=SubmissionInEvaluation(
            id=submission.id,
            content=submission.content,
            time_spent_seconds=submission.time_spent_seconds,
            task=TaskInEvaluation(
                id=task.id if task else 0,
                title=task.title if task else "알 수 없음",
                category=task.category if task else "",
                difficulty=task.difficulty if task else "",
                company=company_brief,
                job_role=job_role_brief,
            ),
        ),
        thread=ThreadInEvaluation(
            id=thread.id if thread else 0,
            persona_name=thread.persona_name if thread else "알 수 없음",
        ),
        created_at=evaluation.created_at,
    )
    return success_response(response.model_dump())
