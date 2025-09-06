import os
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Disable Kafka for tests before importing app
os.environ["ENABLE_KAFKA"] = "false"
os.environ["POSTGRES_DSN"] = "sqlite:///./test.db"

from app.main import app  # noqa: E402

# Monkeypatch send_transaction
from app import kafka_producer  # noqa: E402


client = TestClient(app)


def test_post_transactions_monkeypatched(monkeypatch):
    async def fake_send(*args, **kwargs):
        return True

    monkeypatch.setattr(kafka_producer, "send_transaction", fake_send)

    payload = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "amount": 123.45,
        "currency": "USD",
        "merchant_id": "m_1",
        "merchant_category": "electronics",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": "web",
        "ip": "10.0.0.1",
        "geo": {"lat": 1.0, "lon": 2.0},
        "device_id": "dev1",
    }

    r = client.post("/transactions", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["enqueued"] is True
    assert data["id"] == payload["transaction_id"]
