from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import ApiResponse, success_response
from src.models.schemas.message import MessageResponse
from src.models.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionCreateResponse,
    SubmissionResponse,
    SubmissionUpdateRequest,
)
from src.models.schemas.thread import ThreadBrief
from src.services import (
    ai_service,
    company_service,
    submission_service,
    task_service,
    thread_service,
)

router = APIRouter(prefix="/submissions", tags=["제출"])


@router.post("", response_model=ApiResponse[SubmissionCreateResponse])
async def create_submission(
    body: SubmissionCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """과제를 제출한다. is_draft=false이면 AI 질의응답 스레드가 생성된다."""
    # 과제 존재 확인
    task = await task_service.get_task_detail(db, body.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "과제를 찾을 수 없습니다"},
        )

    # 이미 제출한 과제인지 확인
    existing = await submission_service.get_user_submission_for_task(db, user_id, body.task_id)
    if existing and not existing.is_draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_SUBMITTED", "message": "이미 제출한 과제입니다"},
        )

    # 기존 draft가 있으면 업데이트
    if existing and existing.is_draft:
        submission = await submission_service.update_submission(
            db,
            existing,
            content=body.content,
            is_draft=body.is_draft,
            time_spent_seconds=body.time_spent_seconds,
        )
    else:
        submission = await submission_service.create_submission(
            db,
            user_id=user_id,
            task_id=body.task_id,
            content=body.content,
            is_draft=body.is_draft,
            time_spent_seconds=body.time_spent_seconds,
        )

    thread_brief = None
    first_message = None

    # 정식 제출이면 AI 질의응답 시작
    if not body.is_draft:
        # 기업, 직무 조회
        companies = await company_service.search_companies(db)
        company = next((c for c in companies if c.id == task.company_id), None)
        company_name = company.name if company else "알 수 없는 기업"

        from src.services import job_role_service

        roles = await job_role_service.search_job_roles(db)
        job_role = next((r for r in roles if r.id == task.job_role_id), None)
        job_role_name = job_role.name if job_role else "알 수 없는 직무"

        # AI 페르소나 생성
        persona = await ai_service.generate_persona(
            company_name=company_name,
            job_role_name=job_role_name,
            task_title=task.title,
        )

        # AI 첫 질문 생성
        first_question = await ai_service.generate_first_question(
            company_name=company_name,
            job_role_name=job_role_name,
            task_title=task.title,
            task_description=task.description,
            submission_content=body.content,
            persona_name=persona["persona_name"],
            persona_department=persona["persona_department"],
        )

        # 스레드 + 첫 메시지 생성
        thread, message = await thread_service.create_thread_with_first_message(
            db,
            submission_id=submission.id,
            user_id=user_id,
            persona_name=persona["persona_name"],
            persona_department=persona["persona_department"],
            topic_tag=persona["topic_tag"],
            total_questions=persona["total_questions"],
            first_message_content=first_question,
        )

        thread_brief = ThreadBrief.model_validate(thread).model_dump()
        first_message = MessageResponse.model_validate(message).model_dump()

    response = SubmissionCreateResponse(
        submission=SubmissionResponse.model_validate(submission),
        thread=ThreadBrief(**thread_brief) if thread_brief else None,
        first_message=MessageResponse(**first_message) if first_message else None,
    )
    return success_response(response.model_dump())


@router.put("/{submission_id}", response_model=ApiResponse[SubmissionResponse])
async def update_submission(
    submission_id: int,
    body: SubmissionUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """제출물을 수정한다 (draft 상태일 때만)."""
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SUBMISSION_NOT_FOUND", "message": "제출물을 찾을 수 없습니다"},
        )
    if submission.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "권한이 없습니다"},
        )
    if not submission.is_draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_SUBMITTED", "message": "이미 제출된 과제는 수정할 수 없습니다"},
        )

    updated = await submission_service.update_submission(
        db,
        submission,
        content=body.content,
        is_draft=body.is_draft,
        time_spent_seconds=body.time_spent_seconds,
    )
    return success_response(SubmissionResponse.model_validate(updated).model_dump())


@router.get("/{submission_id}", response_model=ApiResponse[SubmissionResponse])
async def get_submission(
    submission_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """제출물을 조회한다."""
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SUBMISSION_NOT_FOUND", "message": "제출물을 찾을 수 없습니다"},
        )
    if submission.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "권한이 없습니다"},
        )
    return success_response(SubmissionResponse.model_validate(submission).model_dump())
