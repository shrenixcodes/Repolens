from __future__ import annotations

from app.models import Todo


class TodoStore:
    """In-memory todo storage (a real app would use a database)."""

    def __init__(self) -> None:
        self._todos: dict[int, Todo] = {}
        self._next_id = 1

    def add(self, title: str) -> Todo:
        todo = Todo(id=self._next_id, title=title)
        self._todos[todo.id] = todo
        self._next_id += 1
        return todo

    def complete(self, todo_id: int) -> Todo | None:
        todo = self._todos.get(todo_id)
        if todo is not None:
            todo.done = True
        return todo

    def list_all(self) -> list[Todo]:
        return sorted(self._todos.values(), key=lambda t: t.id)
