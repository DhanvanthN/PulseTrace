from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            future=True,
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _engine


def get_session_local() -> sessionmaker[Session]:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_database_connectivity() -> tuple[bool, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "connected"
    except SQLAlchemyError as exc:
        return False, str(exc)


DbSession = Annotated[Session, Depends(get_db)]