"""Route handlers for the todo API (illustrative -- no real web framework wired up)."""

from __future__ import annotations

from app.store import TodoStore

_store = TodoStore()


def handle_create_todo(title: str) -> dict:
    """POST /todos"""
    todo = _store.add(title)
    return {"id": todo.id, "title": todo.title, "done": todo.done}


def handle_complete_todo(todo_id: int) -> dict:
    """POST /todos/{id}/complete"""
    todo = _store.complete(todo_id)
    if todo is None:
        return {"error": "Todo not found"}
    return {"id": todo.id, "title": todo.title, "done": todo.done}


def handle_list_todos() -> list[dict]:
    """GET /todos"""
    return [{"id": t.id, "title": t.title, "done": t.done} for t in _store.list_all()]
