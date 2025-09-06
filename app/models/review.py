import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class ReviewDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String, ForeignKey("transactions.id"), unique=True, index=True)
    reviewer = Column(String)
    decision = Column(Enum(ReviewDecision))
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_review_tx"),
    )
