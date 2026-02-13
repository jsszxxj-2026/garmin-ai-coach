"""SQLAlchemy engine + session helpers."""

from __future__ import annotations

import logging
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings


logger = logging.getLogger(__name__)


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    global _engine, _SessionLocal

    if _engine is not None:
        return _engine

    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    _engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""

    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_optional() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency that yields a DB session or None when disabled."""

    if not settings.DATABASE_URL:
        yield None
        return

    try:
        yield from get_db()
    except Exception as e:
        logger.error(f"[DB] Failed to create session: {e}")
        yield None


def init_db() -> bool:
    """Create tables if DATABASE_URL is configured."""

    if not settings.DATABASE_URL:
        logger.info("[DB] DATABASE_URL not set; database disabled")
        return False

    from backend.app.db.base import Base
    from backend.app.db import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("[DB] Database tables ensured")
    return True
