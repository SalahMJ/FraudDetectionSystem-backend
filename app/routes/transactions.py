import json
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app import kafka_producer
from app.schemas.transaction import TransactionIn, EnqueueResponse

router = APIRouter(tags=["transactions"])


@router.post("/transactions", response_model=EnqueueResponse)
async def post_transaction(body: TransactionIn) -> EnqueueResponse:
    settings = get_settings()

    # Pydantic v2: ensure datetime/UUID are JSON-serializable
    payload = body.model_dump(mode="json")

    # Ensure transaction_id is a str UUID for Kafka key
    tx_id = str(body.transaction_id)

    enqueued = await kafka_producer.send_transaction(
        topic=settings.KAFKA_TRANSACTIONS_TOPIC, key=tx_id.encode(), value=json.dumps(payload).encode()
    )
    if not enqueued:
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    return EnqueueResponse(enqueued=True, id=body.transaction_id)
