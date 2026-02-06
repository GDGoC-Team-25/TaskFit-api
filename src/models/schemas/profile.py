from datetime import datetime

from pydantic import BaseModel

from src.models.schemas.auth import UserResponse


class UserStats(BaseModel):
    total_solved: int
    avg_score: float
    rank_percentile: float | None = None


class RecentEvaluation(BaseModel):
    id: int
    task_title: str
    total_score: int
    created_at: datetime


class ProfileResponse(BaseModel):
    user: UserResponse
    stats: UserStats
    recent_submissions: list[RecentEvaluation]


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    bio: str | None = None
