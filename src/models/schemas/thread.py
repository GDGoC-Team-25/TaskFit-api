from datetime import datetime

from pydantic import BaseModel

from src.models.schemas.message import MessageResponse


class ThreadBrief(BaseModel):
    id: int
    persona_name: str
    persona_department: str
    topic_tag: str
    status: str
    total_questions: int
    asked_count: int

    model_config = {"from_attributes": True}


class ThreadListItem(BaseModel):
    id: int
    persona_name: str
    persona_department: str
    topic_tag: str
    status: str
    total_questions: int
    asked_count: int
    message_count: int = 0
    last_message_preview: str | None = None
    company_name: str | None = None
    job_role_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ThreadListResponse(BaseModel):
    items: list[ThreadListItem]
    total: int
    page: int
    page_size: int


class SubmissionInThread(BaseModel):
    id: int
    task_id: int
    task_title: str


class EvaluationInThread(BaseModel):
    id: int
    total_score: int
    score_label: str


class ThreadDetailResponse(BaseModel):
    id: int
    persona_name: str
    persona_department: str
    topic_tag: str
    status: str
    total_questions: int
    asked_count: int
    submission: SubmissionInThread
    evaluation: EvaluationInThread | None = None
    messages: list[MessageResponse]
