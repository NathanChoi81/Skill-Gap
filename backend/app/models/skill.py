"""Skill and user-skill models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    parent_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(50), nullable=False, default="hard")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    source = Column(String(50), nullable=False)  # resume, manual, course
    created_at = Column(DateTime, default=datetime.utcnow)


class UserNotInterestedSkill(Base):
    __tablename__ = "user_not_interested_skills"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
