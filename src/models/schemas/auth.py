from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    bio: str | None = None
    profile_image: str | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
