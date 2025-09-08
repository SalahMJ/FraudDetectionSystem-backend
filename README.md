# Backend (FastAPI) — Fraud Detection System

This service powers the Fraud Detection System API: transaction ingestion, scoring (rules + ML), review workflow, stats, auth, and AI insights.

## Prerequisites
- Python 3.10+
- PostgreSQL 14+
- (Optional) Redis 6+
- (Optional) Kafka 3.x

## Quick Start
1) Create a virtualenv and install deps
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Configure environment (copy `.env.example` → `.env` or export shell vars)
- POSTGRES_DSN
- REDIS_URL (optional)
- ENABLE_KAFKA=true|false
- KAFKA_BOOTSTRAP_SERVERS (if Kafka enabled)
- MODEL_PATH (path to Isolation Forest artifact)
- JWT_SECRET
- CORS_ORIGINS
- GEMINI_API_KEY, GEMINI_MODEL (for AI Insights)
3) Initialize database (if needed)
```
psql < ../infra/init.sql
```
4) Run the server
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Layout
- `app/main.py` — FastAPI app factory and router mounts
- `app/config.py` — settings from env
- `app/models/` — SQLAlchemy models and DB session
- `app/routes/` — REST endpoints (auth, fraud, transactions, stats, health)
- `app/services/` — domain services
  - `inference.py` — scikit-learn model loading and scoring
  - `rules.py` — business rules
  - `stats.py` — aggregations (timeseries + totals)
  - `auth.py` — JWT utilities
  - `cache.py` — optional Redis helpers
  - `ai.py` — Gemini integration for insights/chart specs
- `app/kafka_producer.py` / `app/kafka_consumer.py` — optional streaming pipeline
- `scripts/` — `seed.py`, `train_offline.py`

## Core Features
- Transaction ingest via REST and optional Kafka pipeline
- Hybrid decisioning: rules + Isolation Forest anomaly score
- Admin review workflow (approve/reject/pending)
- Windowed stats for KPIs and trends
- AI Insights endpoint: summarization + chart spec JSON

## Endpoints (high-level)
- Auth: `POST /auth/login`
- Transactions/Fraud:
  - `POST /fraud/ingest` — enqueue/store a transaction
  - `GET /fraud/transactions` — list (filters by status)
  - `POST /fraud/review` — approve/reject/pending
- Stats:
  - `GET /stats?window=7d|30d` — timeseries + totals
  - `POST /stats/ai` — returns `{ insight, chartSpec, (optional) chartType }`
- Health: `GET /health`

## Model (scikit-learn)
- Offline training: `scripts/train_offline.py` generates an Isolation Forest artifact (joblib) at `MODEL_PATH`.
- Online inference: `services/inference.py` loads the artifact on startup and scores incoming transactions.
- Rules are combined with model output to form a final decision.

## Kafka (optional)
- Producer publishes to `transactions.in`.
- Consumer reads and calls rules + model, persists decision, and may publish to `decisions.out`.
- Enable with `ENABLE_KAFKA=true` and set `KAFKA_BOOTSTRAP_SERVERS`.

## AI Insights (Gemini)
- Configure `GEMINI_API_KEY` and `GEMINI_MODEL` (e.g., `gemini-2.5-flash`).
- `POST /stats/ai` composes system instructions, attaches current stats JSON, and returns insight + chart spec JSON.

## Testing
```
pytest -q
```

## Security Notes
- JWT-based auth; `JWT_SECRET` required.
- Set `CORS_ORIGINS` to your frontend origin.
- Avoid committing real API keys; use `.env`/secrets.

## Troubleshooting
- DB connection errors → verify `POSTGRES_DSN`, DB up and reachable.
- Kafka not connecting → set `ENABLE_KAFKA=false` for local sync-only demo.
- Model not found → verify `MODEL_PATH` points to an existing artifact.
- AI errors → check `GEMINI_*` and outbound network access.
