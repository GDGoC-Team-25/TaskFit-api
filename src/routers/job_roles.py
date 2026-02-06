from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.response import success_response
from src.models.schemas.job_role import JobRoleResponse
from src.services import job_role_service

router = APIRouter(prefix="/job-roles", tags=["직무"])


@router.get("/categories", response_model=dict)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """직무 카테고리 목록을 반환한다."""
    categories = await job_role_service.get_categories(db)
    return success_response(categories)


@router.get("", response_model=dict)
async def search_job_roles(
    category: str | None = Query(None, description="카테고리 필터"),
    q: str | None = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db),
):
    """직무를 검색한다."""
    roles = await job_role_service.search_job_roles(db, category=category, q=q)
    data = [JobRoleResponse.model_validate(r).model_dump() for r in roles]
    return success_response(data)
