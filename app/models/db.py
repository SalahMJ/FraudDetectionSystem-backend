import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Iterator

from app.config import get_settings, SELECTED_ENV_FILE


settings = get_settings()

# Log which env file and DSN are being used before creating the engine
logging.getLogger(__name__).info(
    "[DB] Using ENV_FILE=%s, POSTGRES_DSN=%s",
    SELECTED_ENV_FILE,
    settings.POSTGRES_DSN,
)

engine = create_engine(settings.POSTGRES_DSN, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
