from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy import text
from sqlalchemy.orm import Session


WINDOW_TO_INTERVAL = {
    "7d": "7 days",
    "30d": "30 days",
}


def compute_stats(db: Session, window: str = "7d") -> Dict:
    interval = WINDOW_TO_INTERVAL.get(window, "7 days")

    timeseries_sql = text(
        """
        SELECT
          date_trunc('day', timestamp) AS ts,
          SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS count_fraud,
          SUM(CASE WHEN is_fraud THEN 0 ELSE 1 END) AS count_clean
        FROM transactions
        WHERE timestamp >= now() - INTERVAL :interval
        GROUP BY 1
        ORDER BY 1
        """
    )

    totals_sql = text(
        """
        SELECT
          SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS fraud_total,
          SUM(CASE WHEN is_fraud THEN 0 ELSE 1 END) AS clean_total,
          SUM(CASE WHEN status = 'PENDING_REVIEW' THEN 1 ELSE 0 END) AS pending_total,
          SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END) AS approved_total,
          SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_total
        FROM transactions
        WHERE timestamp >= now() - INTERVAL :interval
        """
    )

    rows = db.execute(timeseries_sql, {"interval": interval}).mappings().all()
    totals = db.execute(totals_sql, {"interval": interval}).mappings().one()

    return {
        "timeseries": [
            {
                "ts": r["ts"].isoformat(),
                "count_fraud": int(r["count_fraud"] or 0),
                "count_clean": int(r["count_clean"] or 0),
            }
            for r in rows
        ],
        "totals": {k: int(v or 0) for k, v in totals.items()},
    }
