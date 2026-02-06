from datetime import datetime

from pydantic import BaseModel


class WeeklySummary(BaseModel):
    score_percentage: float
    problems_solved: int
    avg_time_minutes: float
    weak_tag_count: int


class AiInsight(BaseModel):
    improvements: str
    weak_areas: str


class RecentSubmission(BaseModel):
    id: int
    task_title: str
    category: str
    total_score: int | None = None
    is_correct: bool | None = None
    time_spent_seconds: int | None = None
    created_at: datetime


class CompetencySummary(BaseModel):
    company_name: str
    job_role_name: str
    avg_score: float
    attempt_count: int
    weak_tags: list[str] | None = None


class DashboardSummaryResponse(BaseModel):
    weekly_summary: WeeklySummary
    ai_insight: AiInsight
    recent_submissions: list[RecentSubmission]
    competencies: list[CompetencySummary]
