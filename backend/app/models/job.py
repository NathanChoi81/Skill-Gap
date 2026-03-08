"""Job posting, job_skills, and role_aggregates models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.db import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True)
    title_original = Column(String(500), nullable=False)
    pdf_text = Column(Text, nullable=False)
    degree_required = Column(String(255), nullable=True)
    experience_required = Column(String(255), nullable=True)
    what_you_will_do_excerpt = Column(Text, nullable=True)
    derived_by = Column(String(50), nullable=False)  # ai, fallback, manual_override
    created_at = Column(DateTime, default=datetime.utcnow)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    skill_type = Column(String(50), primary_key=True)  # required, preferred, description


class RoleAggregate(Base):
    __tablename__ = "role_aggregates"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    aggregated_skill_frequency_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
