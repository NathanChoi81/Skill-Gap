"""Role and user-role models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.db import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    last_selected_at = Column(DateTime, nullable=True)


class UserActiveRole(Base):
    __tablename__ = "user_active_role"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True)
    set_at = Column(DateTime, default=datetime.utcnow)
