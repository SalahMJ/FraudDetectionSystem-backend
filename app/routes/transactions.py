import json
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app import kafka_producer
from app.schemas.transaction import TransactionIn, EnqueueResponse
from app.models.db import SessionLocal
from app.models import Transaction, TransactionStatus
from app.services.cache import get_cache
from app.services.inference import FraudModel
from app.services import rules

router = APIRouter(tags=["transactions"])


@router.post("/transactions", response_model=EnqueueResponse)
async def post_transaction(body: TransactionIn) -> EnqueueResponse:
    settings = get_settings()

    # Pydantic v2: ensure datetime/UUID are JSON-serializable
    payload = body.model_dump(mode="json")

    # Ensure transaction_id is a str UUID for Kafka key
    tx_id = str(body.transaction_id)

    # Rule-based pre-checks
    rules_flag, reasons = rules.evaluate_transaction(payload)
    # Model scoring
    model = FraudModel.instance()
    score, model_flag = model.predict_from_transaction(payload)
    is_fraud = bool(rules_flag or model_flag)

    enqueued = await kafka_producer.send_transaction(
        topic=settings.KAFKA_TRANSACTIONS_TOPIC, key=tx_id.encode(), value=json.dumps(payload).encode()
    )
    if not enqueued:
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    return EnqueueResponse(enqueued=True, id=body.transaction_id)
