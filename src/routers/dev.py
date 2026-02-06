from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import create_access_token
from src.core.database import get_db
from src.core.response import success_response
from src.services import ai_service, user_service

router = APIRouter(prefix="/dev", tags=["개발용"])


class DevTokenRequest(BaseModel):
    user_id: int


class DevCreateUserRequest(BaseModel):
    google_id: str = "test_google_id"
    email: str = "test@example.com"
    name: str = "테스트 유저"


class DevAiTaskRequest(BaseModel):
    company_name: str = "토스"
    job_role_name: str = "백엔드 개발자"
    count: int = 3


class DevAiPersonaRequest(BaseModel):
    company_name: str = "토스"
    job_role_name: str = "백엔드 개발자"
    task_title: str = "결제 시스템 API 설계"


class DevAiEvalRequest(BaseModel):
    company_name: str = "토스"
    job_role_name: str = "백엔드 개발자"
    task_title: str = "결제 시스템 API 설계"
    task_description: str = "결제 시스템의 REST API를 설계하세요."
    submission_content: str = "POST /payments 엔드포인트를 만들었습니다."
    conversation_history: list[dict] = []


@router.post("/auth/token", response_model=dict)
async def create_dev_token(body: DevTokenRequest):
    """개발용 JWT 토큰을 발급한다."""
    token = create_access_token(body.user_id)
    return success_response({"access_token": token, "token_type": "bearer"})


@router.post("/auth/create-test-user", response_model=dict)
async def create_test_user(
    body: DevCreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """테스트 유저를 생성한다."""
    existing = await user_service.get_user_by_google_id(db, body.google_id)
    if existing:
        return success_response({"id": existing.id, "message": "이미 존재하는 유저입니다"})

    user = await user_service.create_user(
        db,
        google_id=body.google_id,
        email=body.email,
        name=body.name,
    )
    return success_response({"id": user.id, "message": "유저가 생성되었습니다"})


@router.post("/ai/generate-tasks", response_model=dict)
async def test_generate_tasks(body: DevAiTaskRequest):
    """AI 과제 생성을 테스트한다."""
    result = await ai_service.generate_tasks(
        company_name=body.company_name,
        job_role_name=body.job_role_name,
        count=body.count,
    )
    return success_response(result)


@router.post("/ai/generate-persona", response_model=dict)
async def test_generate_persona(body: DevAiPersonaRequest):
    """AI 페르소나 생성을 테스트한다."""
    result = await ai_service.generate_persona(
        company_name=body.company_name,
        job_role_name=body.job_role_name,
        task_title=body.task_title,
    )
    return success_response(result)


@router.post("/ai/evaluate", response_model=dict)
async def test_evaluate(body: DevAiEvalRequest):
    """AI 채점을 테스트한다."""
    result = await ai_service.evaluate_submission(
        company_name=body.company_name,
        job_role_name=body.job_role_name,
        task_title=body.task_title,
        task_description=body.task_description,
        key_points=None,
        submission_content=body.submission_content,
        conversation_history=body.conversation_history,
    )
    return success_response(result)
