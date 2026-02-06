from datetime import datetime

from pydantic import BaseModel


class MessageCreateRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    message_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    user_message: MessageResponse
    ai_message: MessageResponse | None = None
    thread: "ThreadStatus"
    evaluation: "EvaluationInline | None" = None


class ThreadStatus(BaseModel):
    status: str
    asked_count: int
    total_questions: int


class EvaluationInline(BaseModel):
    id: int
    total_score: int
    score_label: str
    scores_detail: list[dict]
    ai_summary: str
    analysis_points: dict
