from __future__ import annotations


# =========================================================
# SQLAlchemy Imports
# =========================================================

# Database column/data types.
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

# ORM relationship handling.
from sqlalchemy.orm import relationship

# SQL functions like NOW().
from sqlalchemy.sql import func


# Base ORM class from database.py
from src.db.database import Base


# =========================================================
# User Table
# =========================================================

class User(Base):
    """
    Stores registered application users.
    """

    # Database table name.
    __tablename__ = "users"

    # Primary key.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Unique user email.
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # Hashed password only.
    password_hash = Column(
        String(255),
        nullable=False,
    )

    # Optional full name.
    full_name = Column(
        String(255),
        nullable=True,
    )

    # Account creation timestamp.
    created_at = Column(
        DateTime(timezone=True),

        # Automatically set creation time.
        server_default=func.now(),
    )

    # ----------------------------------------
    # Relationships
    # ----------------------------------------

    # One-to-many relationship:
    # User → CandidateProfileRecord (multiple profiles per user)
    profiles = relationship(

        "CandidateProfileRecord",

        # Reverse relationship name.
        back_populates="user",

        # One user can have many profiles.
        uselist=True,

        # Delete all profiles automatically if user is deleted.
        cascade="all, delete-orphan",
    )

    # One-to-one relationship:
    # User → UserPreferenceRecord
    preferences = relationship(

        "UserPreferenceRecord",

        back_populates="user",

        uselist=False,

        cascade="all, delete-orphan",
    )


# =========================================================
# Candidate Profile Table
# =========================================================

class CandidateProfileRecord(Base):
    """
    Stores saved candidate profiles for users.
    """

    __tablename__ = "candidate_profiles"

    # Primary key.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Foreign key linking to users table.
    # No unique=True — one user can have many profiles.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    # System-generated UUID — never editable by the user.
    candidate_id = Column(
        String(36),
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )

    # Human-readable profile label chosen by the user,
    # e.g. "Data Scientist Profile" or "ML Engineer Profile".
    profile_name = Column(
        String(100),
        nullable=False,
        default="My Profile",
    )

    full_name = Column(
        String(255),
        nullable=True,
    )

    current_title = Column(
        String(255),
        nullable=True,
    )

    location = Column(
        String(255),
        nullable=True,
    )

    education = Column(
        String(50),
        nullable=True,
    )

    years_experience = Column(
        Integer,
        nullable=True,
    )

    # ----------------------------------------
    # JSON-stored list fields
    # ----------------------------------------

    # Lists stored as JSON strings.
    skills_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    tools_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    domains_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    certifications_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    projects_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    # Seniority level.
    seniority = Column(
        String(50),
        nullable=True,
    )

    # Free-text candidate summary.
    summary = Column(
        Text,
        nullable=True,
    )

    # Last update timestamp.
    updated_at = Column(
        DateTime(timezone=True),

        server_default=func.now(),

        # Automatically updates timestamp on modification.
        onupdate=func.now(),
    )

    # Reverse relationship:
    # CandidateProfileRecord → User
    user = relationship(
        "User",
        back_populates="profiles",
    )


# =========================================================
# User Preferences Table
# =========================================================

class UserPreferenceRecord(Base):
    """
    Stores saved recommendation preferences for users.
    """

    __tablename__ = "user_preferences"

    # Primary key.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Foreign key to users table.
    user_id = Column(

        Integer,

        ForeignKey("users.id"),

        # One preference record per user.
        unique=True,

        nullable=False,
    )

    # ----------------------------------------
    # Preference fields stored as JSON strings
    # ----------------------------------------

    preferred_titles_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    preferred_locations_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    preferred_workplace_types_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    preferred_domains_json = Column(
        Text,
        nullable=True,
        default="[]",
    )

    # Preferred seniority.
    preferred_seniority = Column(
        String(50),
        nullable=True,
    )

    # Minimum acceptable recommendation score.
    min_score = Column(
        Integer,
        nullable=True,
        default=50,
    )

    # Last update timestamp.
    updated_at = Column(
        DateTime(timezone=True),

        server_default=func.now(),

        onupdate=func.now(),
    )

    # Reverse relationship:
    # UserPreferenceRecord → User
    user = relationship(
        "User",
        back_populates="preferences",
    )


# =========================================================
# Password Reset Token Table
# =========================================================

class PasswordResetToken(Base):
    """
    Stores one-time password reset tokens.
    Tokens are hashed (SHA-256) before storage.
    Each token expires after 1 hour and is single-use.
    """

    __tablename__ = "password_reset_tokens"

    # Primary key.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Foreign key linking to users table.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # SHA-256 hash of the raw token (never store the raw token).
    token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Token expiration timestamp (UTC).
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Whether this token has already been used.
    used = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Creation timestamp.
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )