import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine which .env file to load
_env_file_candidates = (".env", "app/.env", "/app/.env")
ENV_FILE = os.getenv("ENV_FILE")
if ENV_FILE:
    # Normalize relative path
    if not os.path.isabs(ENV_FILE):
        ENV_FILE = os.path.abspath(ENV_FILE)
    # If provided path doesn't exist, try fallbacks
    if not os.path.exists(ENV_FILE):
        for candidate in _env_file_candidates:
            if os.path.exists(candidate):
                ENV_FILE = candidate
                break
        else:
            ENV_FILE = ".env"
else:
    for candidate in _env_file_candidates:
        if os.path.exists(candidate):
            ENV_FILE = candidate
            break
    else:
        # Fallback to a relative .env even if it doesn't exist; pydantic-settings
        # will simply not load it if missing
        ENV_FILE = ".env"

# Expose which env file was ultimately selected (optional to log in main)
SELECTED_ENV_FILE = ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unrelated env vars (e.g., API_URL used by scripts)
    )
    # Core services
    POSTGRES_DSN: str = Field(
        default="postgresql+psycopg2://app:app@postgres:5432/frauddb",
        description="SQLAlchemy DSN for Postgres",
    )
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092")
    ENABLE_KAFKA: bool = Field(default=True)

    # Topics
    KAFKA_TRANSACTIONS_TOPIC: str = Field(default="transactions")

    # Auth
    JWT_SECRET: str = Field(default="devsecret")
    ADMIN_USER: str = Field(default="admin")
    ADMIN_PASSWORD: str = Field(default="admin")

    # Model
    MODEL_PATH: str = Field(default="/app/app/models/artifacts/iforest.pkl")
    IFOREST_THRESHOLD: float = Field(default=-0.2, description="Anomaly if score < threshold")

    # Risk rules (simple pre-checks before ML)
    ENABLE_RULES: bool = Field(default=True, description="Enable rule-based pre-checks")
    AMOUNT_HARD_MAX: float = Field(
        default=1_000_000.0, description="Amounts strictly above this are auto-flagged as fraud"
    )
    HIGH_RISK_CATEGORIES: str = Field(
        default="jewelry,crypto",
        description="Comma-separated categories considered high-risk; used by rules",
    )

    # API
    LOG_LEVEL: str = Field(default="INFO")
    CORS_ORIGINS: str = Field(default="http://localhost:4200")

    # GenAI (Gemini)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model name")

    # pydantic-settings v2 uses model_config above


@lru_cache()
def get_settings() -> Settings:
    return Settings()
