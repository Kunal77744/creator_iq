"""SQLAlchemy database engine, session factory, and FastAPI session dependency."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

# Allow multi-threaded access when using SQLite (e.g., in tests)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Create the SQLAlchemy engine with connection health checks and recycling
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """Yield a database session per request and ensure it is closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
