import os
from fastapi.testclient import TestClient

# Disable Kafka for tests before importing app
os.environ["ENABLE_KAFKA"] = "false"
os.environ["POSTGRES_DSN"] = "sqlite:///./test.db"

from app.main import app  # noqa: E402


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
