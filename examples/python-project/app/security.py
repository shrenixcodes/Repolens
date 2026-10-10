"""Password hashing and JWT-like token helpers (simplified for this example)."""

from __future__ import annotations

import hashlib
import hmac
import time

_SECRET = "example-secret-do-not-use-in-production"


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash."""
    return hmac.compare_digest(hash_password(password), password_hash)


def create_token(user_id: int) -> str:
    """Create a simple signed token for user_id (not a real JWT -- illustrative)."""
    payload = f"{user_id}:{int(time.time())}"
    signature = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_token(token: str) -> int | None:
    """Return the user_id encoded in token, or None if invalid."""
    try:
        user_id_str, timestamp_str, signature = token.split(":")
    except ValueError:
        return None
    payload = f"{user_id_str}:{timestamp_str}"
    expected = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return int(user_id_str)
