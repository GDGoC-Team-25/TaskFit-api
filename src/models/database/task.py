from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database.base import Base


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_company_job", "company_id", "job_role_id"),
        {"schema": "taskfit"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_role_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    key_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tech_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
