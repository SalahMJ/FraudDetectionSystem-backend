import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Boolean,
    Enum,
    Index,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class TransactionStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, index=True)

    amount = Column(Numeric)
    currency = Column(String)
    merchant_id = Column(String)
    merchant_category = Column(String)
    timestamp = Column(DateTime(timezone=True), index=True)
    channel = Column(String)
    ip = Column(String)
    lat = Column(Numeric, nullable=True)
    lon = Column(Numeric, nullable=True)
    device_id = Column(String, nullable=True)

    score = Column(Float, nullable=True)
    is_fraud = Column(Boolean, default=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING_REVIEW, index=True)

    __table_args__ = (
        Index("ix_user_ts", "user_id", "timestamp"),
        Index("ix_is_fraud", "is_fraud"),
    )
