from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database.base import Base


class UserCompetency(Base):
    __tablename__ = "user_competencies"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "job_role_id", name="uq_user_competencies"),
        {"schema": "taskfit"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_role_id: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weak_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
