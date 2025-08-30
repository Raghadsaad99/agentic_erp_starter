# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./erp_v2.db"

# For SQLite, disable same-thread check
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Use this Base for all your models' metadata
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
