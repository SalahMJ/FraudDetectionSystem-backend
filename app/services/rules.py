from __future__ import annotations
from typing import List, Tuple

from app.config import get_settings


def _normalize_category(cat: str | None) -> str:
    if not cat:
        return ""
    return cat.strip().lower()


def evaluate_transaction(payload: dict) -> Tuple[bool, List[str]]:
    """
    Simple rule-based checks to complement ML.

    Rules:
    - Amount hard max: if amount > AMOUNT_HARD_MAX => fraud
    - High-risk categories: if category in HIGH_RISK_CATEGORIES and amount >= 1000 => fraud

    Returns (is_fraud_by_rules, reasons)
    """
    settings = get_settings()
    if not settings.ENABLE_RULES:
        return False, []

    reasons: List[str] = []
    try:
        amount = float(payload.get("amount", 0.0))
    except Exception:
        amount = 0.0

    category = _normalize_category(payload.get("merchant_category"))
    high_risk_categories = {c.strip().lower() for c in settings.HIGH_RISK_CATEGORIES.split(",") if c.strip()}

    # Rule 1: amount exceeds hard maximum
    if amount > float(settings.AMOUNT_HARD_MAX):
        reasons.append(f"amount>{settings.AMOUNT_HARD_MAX}")

    # Rule 2: high-risk category with significant amount
    if category and category in high_risk_categories and amount >= 1000:
        reasons.append(f"high_risk_category:{category}")

    return (len(reasons) > 0), reasons
