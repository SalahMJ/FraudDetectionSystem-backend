from typing import Optional
from pydantic import BaseModel
from app.models.review import ReviewDecision


class ReviewIn(BaseModel):
    decision: ReviewDecision
    notes: Optional[str] = None


class OkResponse(BaseModel):
    ok: bool
