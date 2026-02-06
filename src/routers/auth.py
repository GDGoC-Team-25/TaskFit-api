import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import create_access_token, get_current_user_id
from src.core.config import get_settings
from src.core.database import get_db
from src.core.response import ApiResponse, success_response
from src.models.schemas.auth import GoogleLoginRequest, TokenResponse, UserResponse
from src.services import user_service

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/google", response_model=ApiResponse[TokenResponse])
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Google ID 토큰으로 로그인/회원가입한다."""
    settings = get_settings()

    # Google tokeninfo로 id_token 검증
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": body.id_token},
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 Google 토큰입니다"},
        )

    token_info = resp.json()

    # audience 검증 (웹 + 모바일 Client ID 모두 허용)
    allowed_audiences = {settings.google_client_id, settings.google_client_id_mobile} - {""}
    if token_info.get("aud") not in allowed_audiences:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_AUDIENCE", "message": "토큰의 audience가 일치하지 않습니다"},
        )

    google_id = token_info["sub"]
    email = token_info["email"]
    name = token_info.get("name", email.split("@")[0])
    picture = token_info.get("picture")

    # 유저 조회 또는 생성
    user = await user_service.get_user_by_google_id(db, google_id)
    if not user:
        user = await user_service.create_user(
            db,
            google_id=google_id,
            email=email,
            name=name,
            profile_image=picture,
        )

    access_token = create_access_token(user.id)
    token_response = TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
    return success_response(token_response.model_dump())


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """현재 로그인한 유저 정보를 반환한다."""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다"},
        )
    return success_response(UserResponse.model_validate(user).model_dump())
