from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.response import success_response
from src.models.schemas.company import CompanyResponse
from src.services import company_service

router = APIRouter(prefix="/companies", tags=["기업"])


@router.get("", response_model=dict)
async def search_companies(
    q: str | None = Query(None, description="검색어"),
    limit: int = Query(20, ge=1, le=100, description="최대 반환 수"),
    db: AsyncSession = Depends(get_db),
):
    """기업을 검색한다."""
    companies = await company_service.search_companies(db, q=q, limit=limit)
    data = [CompanyResponse.model_validate(c).model_dump() for c in companies]
    return success_response(data)
