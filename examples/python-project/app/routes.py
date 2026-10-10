"""Route handlers (illustrative -- no real web framework wired up)."""

from __future__ import annotations

from app.auth import AuthError, AuthService
from app.models import UserRepository
from app.security import verify_token

_users = UserRepository()
_auth = AuthService(_users)


def handle_register(email: str, password: str) -> dict:
    """POST /register"""
    user = _auth.register(email, password)
    return {"id": user.id, "email": user.email}


def handle_login(email: str, password: str) -> dict:
    """POST /login"""
    try:
        token = _auth.login(email, password)
    except AuthError as exc:
        return {"error": str(exc)}
    return {"token": token}


def handle_profile(token: str) -> dict:
    """GET /profile -- requires a valid auth token."""
    user_id = verify_token(token)
    if user_id is None:
        return {"error": "Invalid or expired token"}
    user = _users.find_by_id(user_id)
    if user is None:
        return {"error": "User not found"}
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}
