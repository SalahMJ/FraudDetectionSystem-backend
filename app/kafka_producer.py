from typing import Optional

from aiokafka import AIOKafkaProducer

from app.config import get_settings

_producer: Optional[AIOKafkaProducer] = None


async def start_producer() -> None:
    global _producer
    settings = get_settings()
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await _producer.start()


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


async def send_transaction(topic: str, key: bytes, value: bytes) -> bool:
    global _producer
    if _producer is None:
        # Kafka disabled or not ready
        return False
    try:
        await _producer.send_and_wait(topic, value=value, key=key)
        return True
    except Exception:
        return False
