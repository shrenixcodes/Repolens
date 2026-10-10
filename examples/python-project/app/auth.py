"""Authentication: registration and login."""

from __future__ import annotations

from app.models import User, UserRepository
from app.security import create_token, hash_password, verify_password


class AuthError(Exception):
    """Raised when registration or login fails."""


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def register(self, email: str, password: str) -> User:
        if self._users.find_by_email(email) is not None:
            raise AuthError(f"Email already registered: {email}")
        return self._users.create(email=email, password_hash=hash_password(password))

    def login(self, email: str, password: str) -> str:
        """Verify credentials and return an auth token."""
        user = self._users.find_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")
        return create_token(user.id)
