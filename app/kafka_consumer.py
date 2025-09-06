import asyncio
import json
import uuid
from typing import Optional

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Transaction, TransactionStatus
from app.models.db import SessionLocal
from app.services.cache import get_cache
from datetime import datetime


class KafkaConsumerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self.consumer is not None:
            return
        self.consumer = AIOKafkaConsumer(
            self.settings.KAFKA_TRANSACTIONS_TOPIC,
            bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="fraud-consumer",
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        await self.consumer.start()
        self._stopping.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stopping.set()
        if self._task:
            await self._task
        if self.consumer is not None:
            await self.consumer.stop()
            self.consumer = None

    async def _run_loop(self) -> None:
        assert self.consumer is not None
        cache = get_cache()
        # Lazy import to keep tests lightweight when Kafka is disabled
        from app.services.inference import FraudModel
        model = FraudModel.instance()

        try:
            while not self._stopping.is_set():
                try:
                    msg = await asyncio.wait_for(self.consumer.getone(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                try:
                    payload = json.loads(msg.value)
                except Exception:
                    continue
                # Compute inference synchronously (fast)
                score, is_fraud = model.predict_from_transaction(payload)
                tx_id = str(payload.get("transaction_id"))

                # Upsert in DB in a thread to avoid blocking loop
                await asyncio.to_thread(self._upsert_transaction, payload, score, is_fraud)

                # Push to Redis if flagged
                if is_fraud:
                    await cache.push_flagged(tx_id, payload)
        except asyncio.CancelledError:
            pass

    def _parse_ts(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _upsert_transaction(self, payload: dict, score: float, is_fraud: bool) -> None:
        db: Session = SessionLocal()
        try:
            tx_id = str(payload.get("transaction_id"))
            t = db.query(Transaction).filter(Transaction.id == tx_id).one_or_none()
            if t is None:
                t = Transaction(
                    id=tx_id,
                    user_id=str(payload.get("user_id")),
                    amount=payload.get("amount"),
                    currency=payload.get("currency"),
                    merchant_id=payload.get("merchant_id"),
                    merchant_category=payload.get("merchant_category"),
                    timestamp=self._parse_ts(payload.get("timestamp")),
                    channel=payload.get("channel"),
                    ip=payload.get("ip"),
                    lat=(payload.get("geo", {}) or {}).get("lat"),
                    lon=(payload.get("geo", {}) or {}).get("lon"),
                    device_id=payload.get("device_id"),
                )
                db.add(t)

            t.score = score
            t.is_fraud = is_fraud
            # Auto-approve clean transactions for demo
            t.status = TransactionStatus.PENDING_REVIEW if is_fraud else TransactionStatus.APPROVED

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


_consumer_service: Optional[KafkaConsumerService] = None


async def start_consumer() -> None:
    global _consumer_service
    if _consumer_service is None:
        _consumer_service = KafkaConsumerService()
        await _consumer_service.start()


async def stop_consumer() -> None:
    global _consumer_service
    if _consumer_service is not None:
        await _consumer_service.stop()
        _consumer_service = None
