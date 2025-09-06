from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.transaction import TransactionStatus


class Geo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None


class TransactionIn(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant_id: str
    merchant_category: str
    timestamp: datetime
    channel: str
    ip: str
    geo: Optional[Geo] = Field(default=None)
    device_id: Optional[str] = None


class EnqueueResponse(BaseModel):
    enqueued: bool
    id: str


class TransactionListItem(BaseModel):
    id: str
    user_id: str
    amount: Optional[float]
    currency: Optional[str]
    merchant_id: Optional[str]
    merchant_category: Optional[str]
    timestamp: Optional[datetime]
    score: Optional[float]
    status: TransactionStatus


class TransactionDetail(BaseModel):
    id: str
    user_id: str
    amount: Optional[float]
    currency: Optional[str]
    merchant_id: Optional[str]
    merchant_category: Optional[str]
    timestamp: Optional[datetime]
    channel: Optional[str]
    ip: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    device_id: Optional[str]
    score: Optional[float]
    is_fraud: Optional[bool]
    status: TransactionStatus
