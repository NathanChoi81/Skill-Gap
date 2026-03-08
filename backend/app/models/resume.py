"""Resume model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String
from app.db import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    encrypted_redacted_text = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
