"""SQLAlchemy database infrastructure for EthosOS.

Provides:
- Base class for declarative models
- Engine creation
- Session factory with context manager pattern
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from ethos_os.config import get_settings

# Create Base for declarative models
# Models will import this from db and map to it
Base = declarative_base()


def _import_models() -> None:
    """Import all models to register them with Base.metadata."""
    import ethos_os.models.portfolio  # noqa: F401
    import ethos_os.models.program  # noqa: F401
    import ethos_os.models.project  # noqa: F401
    import ethos_os.models.sprint  # noqa: F401
    import ethos_os.models.task  # noqa: F401
    import ethos_os.models.prd  # noqa: F401
    import ethos_os.models.gate  # noqa: F401
    import ethos_os.models.audit  # noqa: F401
    import ethos_os.execution.agent  # noqa: F401
    import ethos_os.execution.heartbeat  # noqa: F401


# Call after Base is created
_import_models()


def create_engine_from_config() -> engine.Engine:
    """Create SQLAlchemy engine from config."""
    settings = get_settings()
    engine_kwargs = {
        "echo": settings.debug,
        "connect_args": {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    }
    return create_engine(settings.database_url, **engine_kwargs)


# Module-level engine (lazily created)
_engine: engine.Engine | None = None


def get_engine() -> engine.Engine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine_from_config()
    return _engine


def dispose_engine() -> None:
    """Dispose of the engine connection pool."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_session_factory() -> sessionmaker:
    """Get the session factory."""
    return sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic commit/rollback.
    
    Usage:
        with get_session() as session:
            session.add(model)
        # Automatic commit on success, rollback on exception
    
    Yields:
        SQLAlchemy Session
    """
    factory = get_session_factory()
    session = factory()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=get_engine())


def drop_tables() -> None:
    """Drop all tables in the database."""
    Base.metadata.drop_all(bind=get_engine())