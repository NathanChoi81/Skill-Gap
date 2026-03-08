"""Token blacklist: store and check hashed refresh tokens."""
import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import TokenBlacklist


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def add_to_blacklist(db: Session, refresh_token: str, expires_at: datetime) -> None:
    h = hash_refresh_token(refresh_token)
    entry = TokenBlacklist(refresh_token_hash=h, expires_at=expires_at)
    db.add(entry)
    db.commit()


def is_blacklisted(db: Session, refresh_token: str) -> bool:
    h = hash_refresh_token(refresh_token)
    return db.query(TokenBlacklist).filter(TokenBlacklist.refresh_token_hash == h).first() is not None
