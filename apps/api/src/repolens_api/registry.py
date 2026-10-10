"""A small, persistent registry of repositories the API knows about.

Registering a repository only records its absolute path -- nothing is
copied, scanned, or uploaded until `POST /repositories/{id}/index` is
called. The registry is a flat JSON file so the API has no mandatory
external database dependency for this bookkeeping.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DEFAULT_REGISTRY_PATH = Path.home() / ".repolens" / "workspaces.json"


@dataclass(frozen=True, slots=True)
class RepositoryRecord:
    id: str
    path: str
    created_at: str


class RepositoryRegistry:
    def __init__(self, storage_path: Path = DEFAULT_REGISTRY_PATH) -> None:
        self._storage_path = storage_path
        self._lock = Lock()
        self._records: dict[str, RepositoryRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self._storage_path.is_file():
            return
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for entry in raw.get("repositories", []):
            record = RepositoryRecord(**entry)
            self._records[record.id] = record

    def _save(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"repositories": [asdict(r) for r in self._records.values()]}
        self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def register(self, path: Path) -> RepositoryRecord:
        resolved = str(path.resolve())
        with self._lock:
            for record in self._records.values():
                if record.path == resolved:
                    return record
            record = RepositoryRecord(
                id=uuid.uuid4().hex,
                path=resolved,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._records[record.id] = record
            self._save()
            return record

    def get(self, repository_id: str) -> RepositoryRecord | None:
        return self._records.get(repository_id)

    def list(self) -> list[RepositoryRecord]:
        return sorted(self._records.values(), key=lambda r: r.created_at)

    def remove(self, repository_id: str) -> bool:
        with self._lock:
            if repository_id not in self._records:
                return False
            del self._records[repository_id]
            self._save()
            return True
