import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, SELECTED_ENV_FILE
from app.kafka_consumer import start_consumer, stop_consumer
from app.kafka_producer import start_producer, stop_producer
from app.models.db import Base, engine
from app.routes import health as health_router
from app.routes import transactions as transactions_router
from app.routes import auth as auth_router
from app.routes import fraud as fraud_router
from app.routes import stats as stats_router


settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))

# Diagnostics: log which env file and DSN are in use
logging.getLogger(__name__).info(
    "Config loaded from ENV_FILE=%s, POSTGRES_DSN=%s",
    SELECTED_ENV_FILE,
    settings.POSTGRES_DSN,
)

app = FastAPI(title="Fraud Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(transactions_router.router)
app.include_router(fraud_router.router)
app.include_router(stats_router.router)


@app.on_event("startup")
async def on_startup() -> None:
    # Simple init without Alembic for demo
    Base.metadata.create_all(bind=engine)

    if settings.ENABLE_KAFKA:
        await start_producer()
        await start_consumer()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if settings.ENABLE_KAFKA:
        await stop_consumer()
        await stop_producer()
