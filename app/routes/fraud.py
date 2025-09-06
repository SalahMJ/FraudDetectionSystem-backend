from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionStatus, Review, ReviewDecision
from app.models.db import get_db
from app.schemas.review import ReviewIn, OkResponse
from app.schemas.transaction import TransactionDetail, TransactionListItem
from app.services.auth import get_current_user

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.get("/flagged", response_model=List[TransactionListItem])
async def get_flagged(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[TransactionStatus] = Query(None),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    q = db.query(Transaction).filter(Transaction.is_fraud.is_(True))
    if status is not None:
        q = q.filter(Transaction.status == status)
    q = q.order_by(Transaction.timestamp.desc()).limit(limit)
    items = [
        TransactionListItem(
            id=t.id,
            user_id=t.user_id,
            amount=float(t.amount) if t.amount is not None else None,
            currency=t.currency,
            merchant_id=t.merchant_id,
            merchant_category=t.merchant_category,
            timestamp=t.timestamp,
            score=t.score,
            status=t.status,
        )
        for t in q.all()
    ]
    return items


@router.get("/tx/{id}", response_model=TransactionDetail)
async def get_detail(
    id: str,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.id == id).one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return TransactionDetail(
        id=t.id,
        user_id=t.user_id,
        amount=float(t.amount) if t.amount is not None else None,
        currency=t.currency,
        merchant_id=t.merchant_id,
        merchant_category=t.merchant_category,
        timestamp=t.timestamp,
        channel=t.channel,
        ip=t.ip,
        lat=float(t.lat) if t.lat is not None else None,
        lon=float(t.lon) if t.lon is not None else None,
        device_id=t.device_id,
        score=t.score,
        is_fraud=t.is_fraud,
        status=t.status,
    )


@router.post("/review/{id}", response_model=OkResponse)
async def review(
    id: str,
    body: ReviewIn,
    db: Session = Depends(get_db),
    reviewer: str = Depends(get_current_user),
):
    t = db.query(Transaction).filter(Transaction.id == id).one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")

    t.status = (
        TransactionStatus.APPROVED if body.decision == ReviewDecision.APPROVED else TransactionStatus.REJECTED
    )

    existing = db.query(Review).filter(Review.transaction_id == id).one_or_none()
    if existing:
        existing.decision = body.decision
        existing.notes = body.notes
        existing.reviewer = reviewer
    else:
        db.add(
            Review(transaction_id=id, reviewer=reviewer, decision=body.decision, notes=body.notes)
        )

    db.flush()
    return OkResponse(ok=True)
