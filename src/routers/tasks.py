from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import ApiResponse, success_response
from src.models.schemas.company import CompanyBrief
from src.models.schemas.job_role import JobRoleBrief
from src.models.schemas.task import (
    TaskDetailResponse,
    TaskGeneratedItem,
    TaskGenerateRequest,
    TaskListItem,
    TaskListResponse,
)
from src.services import ai_service, company_service, submission_service, task_service

router = APIRouter(prefix="/tasks", tags=["과제"])


@router.post("/generate", response_model=ApiResponse[list[TaskGeneratedItem]])
async def generate_tasks(
    body: TaskGenerateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """AI로 과제를 생성한다."""
    companies = await company_service.search_companies(db)
    company = next((c for c in companies if c.id == body.company_id), None)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": "기업을 찾을 수 없습니다"},
        )

    from src.services import job_role_service

    roles = await job_role_service.search_job_roles(db)
    job_role = next((r for r in roles if r.id == body.job_role_id), None)
    if not job_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_ROLE_NOT_FOUND", "message": "직무를 찾을 수 없습니다"},
        )

    # AI로 과제 생성
    generated = await ai_service.generate_tasks(
        company_name=company.name,
        job_role_name=job_role.name,
        count=body.count,
    )

    # DB에 저장
    tasks_data = [
        {
            "company_id": body.company_id,
            "job_role_id": body.job_role_id,
            "title": t["title"],
            "description": t["description"],
            "category": t["category"],
            "difficulty": t["difficulty"],
            "estimated_minutes": t["estimated_minutes"],
            "answer_type": t.get("answer_type", "text"),
            "key_points": t.get("key_points"),
            "tech_stack": t.get("tech_stack"),
        }
        for t in generated
    ]
    tasks = await task_service.create_tasks_batch(db, tasks_data)

    result = [
        TaskGeneratedItem(
            id=task.id,
            title=task.title,
            category=task.category,
            difficulty=task.difficulty,
            estimated_minutes=task.estimated_minutes,
            answer_type=task.answer_type,
            company=CompanyBrief.model_validate(company),
            job_role=JobRoleBrief.model_validate(job_role),
        ).model_dump()
        for task in tasks
    ]
    return success_response(result)


@router.get("", response_model=ApiResponse[TaskListResponse])
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: int | None = Query(None),
    job_role_id: int | None = Query(None),
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """과제 목록을 조회한다."""
    items, total = await task_service.get_tasks(
        db,
        page=page,
        page_size=page_size,
        company_id=company_id,
        job_role_id=job_role_id,
        category=category,
        difficulty=difficulty,
    )

    task_list = []
    for task in items:
        sub = await submission_service.get_user_submission_for_task(db, user_id, task.id)
        task_item = TaskListItem.model_validate(task)
        task_item.has_submission = sub is not None
        task_list.append(task_item.model_dump())

    response = TaskListResponse(
        items=[TaskListItem(**t) for t in task_list],
        total=total,
        page=page,
        page_size=page_size,
    )
    return success_response(response.model_dump())


@router.get("/{task_id}", response_model=ApiResponse[TaskDetailResponse])
async def get_task_detail(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """과제 상세를 조회한다."""
    task = await task_service.get_task_detail(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "과제를 찾을 수 없습니다"},
        )

    # 관련 데이터 조회
    companies = await company_service.search_companies(db)
    company = next((c for c in companies if c.id == task.company_id), None)

    from src.services import job_role_service

    roles = await job_role_service.search_job_roles(db)
    job_role = next((r for r in roles if r.id == task.job_role_id), None)

    sub = await submission_service.get_user_submission_for_task(db, user_id, task.id)

    my_submission = None
    if sub:
        my_submission = {"id": sub.id, "status": sub.status, "is_draft": sub.is_draft}

    response = TaskDetailResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        category=task.category,
        difficulty=task.difficulty,
        estimated_minutes=task.estimated_minutes,
        answer_type=task.answer_type,
        tech_stack=task.tech_stack,
        company=(
            CompanyBrief(id=company.id, name=company.name)
            if company
            else CompanyBrief(id=0, name="알 수 없음")
        ),
        job_role=(
            JobRoleBrief(id=job_role.id, name=job_role.name)
            if job_role
            else JobRoleBrief(id=0, name="알 수 없음")
        ),
        created_at=task.created_at,
        my_submission=my_submission,
    )
    return success_response(response.model_dump())
