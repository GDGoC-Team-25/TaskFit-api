from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user_id
from src.core.database import get_db
from src.core.response import ApiResponse, success_response
from src.models.schemas.auth import UserResponse
from src.models.schemas.profile import ProfileResponse, ProfileUpdateRequest
from src.services import profile_service

router = APIRouter(prefix="/profile", tags=["프로필"])


@router.get("", response_model=ApiResponse[ProfileResponse])
async def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """내 프로필을 조회한다."""
    data = await profile_service.get_profile(db, user_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다"},
        )

    response = ProfileResponse(
        user=UserResponse.model_validate(data["user"]),
        stats=data["stats"],
        recent_submissions=data["recent_submissions"],
    )
    return success_response(response.model_dump())


@router.patch("", response_model=ApiResponse[UserResponse])
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """프로필을 수정한다."""
    user = await profile_service.update_profile(
        db,
        user_id,
        name=body.name,
        bio=body.bio,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다"},
        )
    return success_response(UserResponse.model_validate(user).model_dump())
