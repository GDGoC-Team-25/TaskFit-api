from datetime import datetime

from pydantic import BaseModel

from src.models.schemas.company import CompanyBrief
from src.models.schemas.job_role import JobRoleBrief


class TaskGenerateRequest(BaseModel):
    company_id: int
    job_role_id: int
    count: int = 5


class TaskListItem(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    estimated_minutes: int
    answer_type: str
    created_at: datetime
    has_submission: bool = False

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskListItem]
    total: int
    page: int
    page_size: int


class SubmissionBrief(BaseModel):
    id: int
    status: str
    is_draft: bool


class TaskDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    estimated_minutes: int
    answer_type: str
    tech_stack: list[str] | None = None
    company: CompanyBrief
    job_role: JobRoleBrief
    created_at: datetime
    my_submission: SubmissionBrief | None = None

    model_config = {"from_attributes": True}


class TaskGeneratedItem(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    estimated_minutes: int
    answer_type: str
    company: CompanyBrief
    job_role: JobRoleBrief
