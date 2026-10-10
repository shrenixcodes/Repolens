"""Data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    """A registered user."""

    id: int
    email: str
    password_hash: str
    is_admin: bool = False


class UserRepository:
    """In-memory user storage (a real app would use a database)."""

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._next_id = 1

    def create(self, email: str, password_hash: str) -> User:
        user = User(id=self._next_id, email=email, password_hash=password_hash)
        self._users[user.id] = user
        self._next_id += 1
        return user

    def find_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None
