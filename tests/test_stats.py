import os
from fastapi.testclient import TestClient

# Disable Kafka for tests before importing app
os.environ["ENABLE_KAFKA"] = "false"
os.environ["POSTGRES_DSN"] = "sqlite:///./test.db"

from app.main import app  # noqa: E402
from app.services.auth import create_access_token  # noqa: E402
from app.services import stats as stats_service  # noqa: E402


client = TestClient(app)


def test_stats_monkeypatched(monkeypatch):
    token = create_access_token("tester")
    def fake_compute(db, window):
        return {"timeseries": [], "totals": {"fraud_total": 0, "clean_total": 0}}

    monkeypatch.setattr(stats_service, "compute_stats", fake_compute)

    r = client.get("/fraud/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["totals"]["fraud_total"] == 0
