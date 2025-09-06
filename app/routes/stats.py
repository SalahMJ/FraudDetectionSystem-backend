from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.services.auth import get_current_user
from app.services.stats import compute_stats

router = APIRouter(prefix="/fraud", tags=["stats"])


@router.get("/stats")
async def stats(
    window: str = Query("7d"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> Dict:
    return compute_stats(db, window)
