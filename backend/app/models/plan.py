"""Plan, plan_skills, plan_skill_courses models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.db import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_plans_user_role"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    deadline_date = Column(Date, nullable=False)
    hours_per_week = Column(Integer, nullable=False, default=5)
    status = Column(String(50), nullable=False, default="active")  # active, paused
    created_at = Column(DateTime, default=datetime.utcnow)


class PlanSkill(Base):
    __tablename__ = "plan_skills"

    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    position = Column(Integer, nullable=False)


class PlanSkillCourse(Base):
    __tablename__ = "plan_skill_courses"

    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    selected = Column(Boolean, nullable=False)
