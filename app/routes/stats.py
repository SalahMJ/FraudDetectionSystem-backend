from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.services.auth import get_current_user
from app.services.stats import compute_stats
from app.services.ai import call_gemini
from pydantic import BaseModel

router = APIRouter(prefix="/fraud", tags=["stats"])


@router.get("/stats")
async def stats(
    window: str = Query("7d"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> Dict:
    return compute_stats(db, window)


class AIRequest(BaseModel):
    prompt: str
    window: str = "7d"


@router.post("/stats/ai")
async def stats_ai(
    body: AIRequest,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> Dict:
    stats = compute_stats(db, body.window)
    result = call_gemini(body.prompt, stats)
    # Pass through the original stats window for client reference
    return {"window": body.window, "insight": result.get("insight"), "chartSpec": result.get("chartSpec")}
