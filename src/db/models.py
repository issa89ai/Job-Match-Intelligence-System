from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("CandidateProfileRecord", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferenceRecord", back_populates="user", uselist=False, cascade="all, delete-orphan")


class CandidateProfileRecord(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    candidate_id = Column(String(255), nullable=False, default="candidate_001")
    full_name = Column(String(255), nullable=True)
    current_title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    education = Column(String(50), nullable=True)
    years_experience = Column(Integer, nullable=True)

    skills_json = Column(Text, nullable=True, default="[]")
    tools_json = Column(Text, nullable=True, default="[]")
    domains_json = Column(Text, nullable=True, default="[]")
    certifications_json = Column(Text, nullable=True, default="[]")
    projects_json = Column(Text, nullable=True, default="[]")

    seniority = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class UserPreferenceRecord(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    preferred_titles_json = Column(Text, nullable=True, default="[]")
    preferred_locations_json = Column(Text, nullable=True, default="[]")
    preferred_workplace_types_json = Column(Text, nullable=True, default="[]")
    preferred_domains_json = Column(Text, nullable=True, default="[]")
    preferred_seniority = Column(String(50), nullable=True)
    min_score = Column(Integer, nullable=True, default=50)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")