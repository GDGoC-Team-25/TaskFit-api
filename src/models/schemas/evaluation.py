from datetime import datetime

from pydantic import BaseModel

from src.models.schemas.company import CompanyBrief
from src.models.schemas.job_role import JobRoleBrief


class ScoreDetail(BaseModel):
    name: str
    score: int


class AnalysisPoints(BaseModel):
    strengths: list[str]
    weaknesses: list[str]


class TaskInEvaluation(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    company: CompanyBrief
    job_role: JobRoleBrief


class SubmissionInEvaluation(BaseModel):
    id: int
    content: str
    time_spent_seconds: int | None = None
    task: TaskInEvaluation


class ThreadInEvaluation(BaseModel):
    id: int
    persona_name: str


class EvaluationDetailResponse(BaseModel):
    id: int
    total_score: int
    score_label: str
    scores_detail: list[ScoreDetail]
    ai_summary: str
    analysis_points: AnalysisPoints
    feedback: str | None = None
    submission: SubmissionInEvaluation
    thread: ThreadInEvaluation
    created_at: datetime
