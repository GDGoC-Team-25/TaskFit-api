from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import success_response
from src.models.schemas.message import (
    ChatResponse,
    EvaluationInline,
    MessageCreateRequest,
    MessageResponse,
    ThreadStatus,
)
from src.models.schemas.thread import (
    EvaluationInThread,
    SubmissionInThread,
    ThreadDetailResponse,
    ThreadListItem,
    ThreadListResponse,
)
from src.services import (
    ai_service,
    company_service,
    evaluation_service,
    submission_service,
    task_service,
    thread_service,
)

router = APIRouter(prefix="/threads", tags=["질의응답"])


@router.get("", response_model=dict)
async def get_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """질의응답 스레드 목록을 조회한다."""
    items, total = await thread_service.get_threads(db, user_id, page=page, page_size=page_size)

    thread_list = []
    for thread in items:
        messages = await thread_service.get_thread_messages(db, thread.id)
        last_msg = messages[-1] if messages else None

        # submission → task → company, job_role
        submission = await submission_service.get_submission(db, thread.submission_id)
        task = await task_service.get_task_detail(db, submission.task_id) if submission else None

        company_name = None
        job_role_name = None
        if task:
            companies = await company_service.search_companies(db)
            company = next((c for c in companies if c.id == task.company_id), None)
            company_name = company.name if company else None

            from src.services import job_role_service

            roles = await job_role_service.search_job_roles(db)
            job_role = next((r for r in roles if r.id == task.job_role_id), None)
            job_role_name = job_role.name if job_role else None

        thread_list.append(
            ThreadListItem(
                id=thread.id,
                persona_name=thread.persona_name,
                persona_department=thread.persona_department,
                topic_tag=thread.topic_tag,
                status=thread.status,
                total_questions=thread.total_questions,
                asked_count=thread.asked_count,
                message_count=len(messages),
                last_message_preview=last_msg.content[:100] if last_msg else None,
                company_name=company_name,
                job_role_name=job_role_name,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
            ).model_dump()
        )

    response = ThreadListResponse(
        items=[ThreadListItem(**t) for t in thread_list],
        total=total,
        page=page,
        page_size=page_size,
    )
    return success_response(response.model_dump())


@router.get("/{thread_id}", response_model=dict)
async def get_thread_detail(
    thread_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """질의응답 스레드 상세를 조회한다."""
    thread = await thread_service.get_thread_detail(db, thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "THREAD_NOT_FOUND", "message": "스레드를 찾을 수 없습니다"},
        )
    if thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "권한이 없습니다"},
        )

    messages = await thread_service.get_thread_messages(db, thread_id)
    submission = await submission_service.get_submission(db, thread.submission_id)
    task = await task_service.get_task_detail(db, submission.task_id) if submission else None
    evaluation = await evaluation_service.get_evaluation_by_submission_id(db, thread.submission_id)

    response = ThreadDetailResponse(
        id=thread.id,
        persona_name=thread.persona_name,
        persona_department=thread.persona_department,
        topic_tag=thread.topic_tag,
        status=thread.status,
        total_questions=thread.total_questions,
        asked_count=thread.asked_count,
        submission=SubmissionInThread(
            id=submission.id,
            task_id=submission.task_id,
            task_title=task.title if task else "알 수 없음",
        ),
        evaluation=EvaluationInThread(
            id=evaluation.id,
            total_score=evaluation.total_score,
            score_label=evaluation.score_label,
        ) if evaluation else None,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )
    return success_response(response.model_dump())


@router.post("/{thread_id}/messages", response_model=dict)
async def add_message(
    thread_id: int,
    body: MessageCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """스레드에 메시지를 추가하고 AI 응답을 받는다."""
    thread = await thread_service.get_thread_detail(db, thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "THREAD_NOT_FOUND", "message": "스레드를 찾을 수 없습니다"},
        )
    if thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "권한이 없습니다"},
        )
    if thread.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "THREAD_COMPLETED", "message": "이미 완료된 스레드입니다"},
        )

    # 현재 메시지 목록
    messages = await thread_service.get_thread_messages(db, thread_id)
    next_order = len(messages) + 1

    # 유저 메시지 저장
    user_message = await thread_service.add_user_message(db, thread_id, body.content, next_order)

    # 관련 데이터 조회
    submission = await submission_service.get_submission(db, thread.submission_id)
    task = await task_service.get_task_detail(db, submission.task_id) if submission else None

    companies = await company_service.search_companies(db)
    company = next((c for c in companies if c.id == task.company_id), None) if task else None
    company_name = company.name if company else "알 수 없는 기업"

    from src.services import job_role_service

    roles = await job_role_service.search_job_roles(db)
    job_role = next((r for r in roles if r.id == task.job_role_id), None) if task else None
    job_role_name = job_role.name if job_role else "알 수 없는 직무"

    conversation_history = [
        {"role": m.role, "content": m.content} for m in messages
    ] + [{"role": "user", "content": body.content}]

    ai_message = None
    evaluation_data = None

    is_last_question = thread.asked_count >= thread.total_questions

    if is_last_question:
        # 마지막 질문에 대한 답변 → 채점
        eval_result = await ai_service.evaluate_submission(
            company_name=company_name,
            job_role_name=job_role_name,
            task_title=task.title if task else "",
            task_description=task.description if task else "",
            key_points=task.key_points if task else None,
            submission_content=submission.content if submission else "",
            conversation_history=conversation_history,
        )

        evaluation = await evaluation_service.create_evaluation(
            db,
            submission_id=thread.submission_id,
            thread_id=thread.id,
            total_score=eval_result["total_score"],
            score_label=eval_result["score_label"],
            scores_detail=eval_result["scores_detail"],
            ai_summary=eval_result["ai_summary"],
            analysis_points=eval_result["analysis_points"],
            feedback=eval_result.get("feedback"),
        )

        # submission 상태 업데이트
        if submission:
            submission.status = "evaluated"
            await db.commit()

        # 역량 업데이트
        if task:
            weak_tags = eval_result.get("analysis_points", {}).get("weaknesses", [])
            await evaluation_service.update_user_competency(
                db,
                user_id=user_id,
                company_id=task.company_id,
                job_role_id=task.job_role_id,
                new_score=eval_result["total_score"],
                weak_tags=weak_tags,
            )

        await thread_service.complete_thread(db, thread)

        evaluation_data = EvaluationInline(
            id=evaluation.id,
            total_score=evaluation.total_score,
            score_label=evaluation.score_label,
            scores_detail=evaluation.scores_detail,
            ai_summary=evaluation.ai_summary,
            analysis_points=evaluation.analysis_points,
        ).model_dump()
    else:
        # 후속 질문 생성
        follow_up = await ai_service.generate_follow_up(
            company_name=company_name,
            job_role_name=job_role_name,
            task_title=task.title if task else "",
            task_description=task.description if task else "",
            submission_content=submission.content if submission else "",
            persona_name=thread.persona_name,
            persona_department=thread.persona_department,
            conversation_history=conversation_history,
            question_number=thread.asked_count + 1,
            total_questions=thread.total_questions,
        )

        ai_message = await thread_service.add_ai_message(db, thread_id, follow_up, next_order + 1)
        await thread_service.increment_asked_count(db, thread)

    response = ChatResponse(
        user_message=MessageResponse.model_validate(user_message),
        ai_message=MessageResponse.model_validate(ai_message) if ai_message else None,
        thread=ThreadStatus(
            status=thread.status,
            asked_count=thread.asked_count,
            total_questions=thread.total_questions,
        ),
        evaluation=EvaluationInline(**evaluation_data) if evaluation_data else None,
    )
    return success_response(response.model_dump())
