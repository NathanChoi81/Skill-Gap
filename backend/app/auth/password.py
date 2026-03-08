"""Password hashing and policy validation."""
import re
from passlib.context import CryptContext

# Use pbkdf2_sha256 to avoid bcrypt backend quirks on some platforms while
# still providing a strong, salted hash.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_policy(password: str) -> tuple[bool, str]:
    """Validate PRD policy: min 12 chars, 1 upper, 1 lower, 1 number. Returns (ok, message)."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must include at least one number"
    return True, ""
