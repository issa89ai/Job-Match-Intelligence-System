from __future__ import annotations


# =========================================================
# SQLAlchemy Imports
# =========================================================

# create_engine:
# creates the database connection engine.
from sqlalchemy import create_engine

# declarative_base:
# base class for ORM models.
#
# sessionmaker:
# factory for database sessions.
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================================================
# Database Configuration
# =========================================================

# SQLite database file path.
#
# sqlite:///./job_match_app.db
#
# means:
# create/use database file:
# job_match_app.db
#
# in current project directory.
DATABASE_URL = "sqlite:///./job_match_app.db"


# =========================================================
# Database Engine
# =========================================================

# Engine is the core connection interface
# between Python and the database.
engine = create_engine(

    DATABASE_URL,

    # SQLite-specific setting.
    #
    # SQLite normally blocks multi-thread access.
    #
    # FastAPI uses multiple threads,
    # so this disables SQLite thread restriction.
    connect_args={
        "check_same_thread": False
    },
)


# =========================================================
# Session Factory
# =========================================================

# SessionLocal creates independent database sessions.
#
# Each API request gets its own session.
SessionLocal = sessionmaker(

    # Changes are committed manually.
    autocommit=False,

    # Prevent automatic flush before queries.
    autoflush=False,

    # Bind sessions to engine.
    bind=engine,
)


# =========================================================
# ORM Base Class
# =========================================================

# Base class inherited by all database models.
#
# Example:
#
# class User(Base):
#     __tablename__ = "users"
#
Base = declarative_base()


# =========================================================
# Database Dependency
# =========================================================

def get_db():
    """
    FastAPI dependency that provides
    a database session per request.
    """

    # Create database session.
    db = SessionLocal()

    try:

        # Provide session to endpoint.
        yield db

    finally:

        # Always close session after request.
        db.close()