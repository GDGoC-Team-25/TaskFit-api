from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database.base import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    thread_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_label: Mapped[str] = mapped_column(String(30), nullable=False)
    scores_detail: Mapped[list] = mapped_column(JSONB, nullable=False)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_points: Mapped[dict] = mapped_column(JSONB, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
