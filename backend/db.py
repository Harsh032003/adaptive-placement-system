import os
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/adaptive_placement",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow():
    return datetime.utcnow()
