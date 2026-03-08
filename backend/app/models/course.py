"""Course and user course progress/meta models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from app.db import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=True)
    difficulty = Column(Integer, nullable=False)  # 1-5
    duration_hours = Column(Float, nullable=False)
    format = Column(String(100), nullable=False)
    popularity_score = Column(Integer, nullable=False)
    url = Column(String(1000), nullable=True)


class UserCourseProgress(Base):
    __tablename__ = "user_course_progress"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    status = Column(String(50), nullable=False)  # in_progress, complete
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCourseMeta(Base):
    __tablename__ = "user_course_meta"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    adjusted_difficulty = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
