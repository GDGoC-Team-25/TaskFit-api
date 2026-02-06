from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database.base import Base


class Thread(Base):
    __tablename__ = "threads"
    __table_args__ = (
        Index("ix_threads_user_id", "user_id"),
        {"schema": "taskfit"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    persona_name: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_department: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="questioning")
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    asked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
