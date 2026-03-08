"""AES-GCM encryption for redacted resume text at rest."""
import os
from base64 import b64decode, b64encode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

settings = get_settings()
# Derive a key from SECRET_KEY for encryption (32 bytes for AES-256)
def _get_key() -> bytes:
    import hashlib
    return hashlib.sha256(settings.secret_key.encode()).digest()


def encrypt_resume_text(plaintext: str) -> bytes:
    """Encrypt redacted resume text. Returns b64(nonce + ciphertext) as bytes for DB."""
    key = _get_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return b64encode(nonce + ct)


def decrypt_resume_text(blob: bytes) -> str:
    """Decrypt stored blob to plaintext."""
    key = _get_key()
    aes = AESGCM(key)
    raw = b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    return aes.decrypt(nonce, ct, None).decode("utf-8")
