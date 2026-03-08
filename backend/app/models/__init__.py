"""SQLAlchemy models - import all so Base.metadata is complete for Alembic."""
from app.db import Base
from app.models.user import User, TokenBlacklist
from app.models.resume import Resume
from app.models.skill import Skill, UserSkill, UserNotInterestedSkill
from app.models.role import Role, UserRole, UserActiveRole
from app.models.job import JobPosting, JobSkill, RoleAggregate
from app.models.course import Course, UserCourseProgress, UserCourseMeta
from app.models.plan import Plan, PlanSkill, PlanSkillCourse

__all__ = [
    "Base",
    "User",
    "TokenBlacklist",
    "Resume",
    "Skill",
    "UserSkill",
    "UserNotInterestedSkill",
    "Role",
    "UserRole",
    "UserActiveRole",
    "JobPosting",
    "JobSkill",
    "RoleAggregate",
    "Course",
    "UserCourseProgress",
    "UserCourseMeta",
    "Plan",
    "PlanSkill",
    "PlanSkillCourse",
]
