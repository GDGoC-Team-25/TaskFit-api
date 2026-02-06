from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import ApiResponse, success_response
from src.models.schemas.dashboard import DashboardSummaryResponse
from src.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["대시보드"])


@router.get("/summary", response_model=ApiResponse[DashboardSummaryResponse])
async def get_dashboard_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """대시보드 요약 정보를 반환한다."""
    data = await dashboard_service.get_dashboard_summary(db, user_id)
    response = DashboardSummaryResponse(**data)
    return success_response(response.model_dump())
