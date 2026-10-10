import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from repolens_api.app import create_app


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


@pytest.fixture
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    registry_path = tmp_path_factory.mktemp("registry") / "workspaces.json"
    app = create_app(registry_path=registry_path)
    return TestClient(app)


def test_git_history_endpoint(client: TestClient, tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    _git(tmp_path, "commit", "-q", "-m", "Initial commit")

    repo_response = client.post("/repositories", json={"path": str(tmp_path)})
    repo_id = repo_response.json()["id"]

    response = client.get(f"/repositories/{repo_id}/git/history", params={"path": "a.py"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["commits"][0]["subject"] == "Initial commit"


def test_git_history_non_git_repo_returns_400(client: TestClient, tmp_path: Path) -> None:
    repo_response = client.post("/repositories", json={"path": str(tmp_path)})
    repo_id = repo_response.json()["id"]
    response = client.get(f"/repositories/{repo_id}/git/history", params={"path": "a.py"})
    assert response.status_code == 400
