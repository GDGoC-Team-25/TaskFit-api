from datetime import datetime

from pydantic import BaseModel

from src.models.schemas.message import MessageResponse
from src.models.schemas.thread import ThreadBrief


class SubmissionCreateRequest(BaseModel):
    task_id: int
    content: str
    is_draft: bool = False
    time_spent_seconds: int | None = None


class SubmissionUpdateRequest(BaseModel):
    content: str
    is_draft: bool = False
    time_spent_seconds: int | None = None


class SubmissionResponse(BaseModel):
    id: int
    task_id: int
    content: str
    is_draft: bool
    status: str
    time_spent_seconds: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubmissionCreateResponse(BaseModel):
    submission: SubmissionResponse
    thread: ThreadBrief | None = None
    first_message: MessageResponse | None = None
