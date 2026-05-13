"""
Setup database SQLAlchemy untuk MySQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings


# Engine MySQL — pool_pre_ping mencegah error koneksi expired
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk semua model SQLAlchemy
Base = declarative_base()


def get_db():
    """Dependency FastAPI untuk inject session DB ke route."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()