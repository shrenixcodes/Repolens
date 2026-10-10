from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from repolens_api.app import create_app


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    # Deliberately outside any test's `tmp_path` (the repo root under test) so
    # indexing a test repository never picks up the registry's own bookkeeping file.
    registry_path = tmp_path_factory.mktemp("registry") / "workspaces.json"
    app = create_app(registry_path=registry_path)
    return TestClient(app)


def _register_and_index(client: TestClient, repo_root: Path) -> str:
    response = client.post("/repositories", json={"path": str(repo_root)})
    assert response.status_code == 200
    repo_id = response.json()["id"]
    index_response = client.post(f"/repositories/{repo_id}/index")
    assert index_response.status_code == 200
    return repo_id


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_repository_requires_existing_directory(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/repositories", json={"path": str(tmp_path / "nope")})
    assert response.status_code == 400


def test_register_is_idempotent_for_same_path(client: TestClient, tmp_path: Path) -> None:
    first = client.post("/repositories", json={"path": str(tmp_path)})
    second = client.post("/repositories", json={"path": str(tmp_path)})
    assert first.json()["id"] == second.json()["id"]


def test_list_repositories(client: TestClient, tmp_path: Path) -> None:
    client.post("/repositories", json={"path": str(tmp_path)})
    response = client.get("/repositories")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_unknown_repository_returns_404(client: TestClient) -> None:
    response = client.get("/repositories/does-not-exist")
    assert response.status_code == 404


def test_status_before_index_returns_409(client: TestClient, tmp_path: Path) -> None:
    repo_response = client.post("/repositories", json={"path": str(tmp_path)})
    repo_id = repo_response.json()["id"]
    response = client.get(f"/repositories/{repo_id}/status")
    assert response.status_code == 409


def test_full_index_search_ask_impact_flow(client: TestClient, tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/auth.py",
        "def verify_jwt_token(token):\n    '''Verifies a JWT auth token.'''\n    return True\n",
    )
    _write(tmp_path, "app/login.py", "from .auth import verify_jwt_token\n")
    repo_id = _register_and_index(client, tmp_path)

    status_response = client.get(f"/repositories/{repo_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["total_files"] == 2

    search_response = client.post(f"/repositories/{repo_id}/search", json={"query": "jwt token"})
    assert search_response.status_code == 200
    assert any(r["file_path"] == "app/auth.py" for r in search_response.json())

    ask_response = client.post(f"/repositories/{repo_id}/ask", json={"question": "jwt token"})
    assert ask_response.status_code == 200
    ask_payload = ask_response.json()
    assert ask_payload["grounded"] is True
    assert any(c["path"] == "app/auth.py" for c in ask_payload["citations"])

    impact_response = client.post(
        f"/repositories/{repo_id}/impact", json={"target": "app/auth.py"}
    )
    assert impact_response.status_code == 200
    impact_payload = impact_response.json()
    assert impact_payload["target_found"] is True
    assert "app/login.py" in impact_payload["direct_dependents"]


def test_graph_endpoint_returns_file_nodes(client: TestClient, tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    _write(tmp_path, "b.py", "from .a import f\n")
    repo_id = _register_and_index(client, tmp_path)

    response = client.get(f"/repositories/{repo_id}/graph")
    assert response.status_code == 200
    payload = response.json()
    paths = {n["path"] for n in payload["nodes"]}
    assert "a.py" in paths
    assert "b.py" in paths


def test_files_list_and_detail(client: TestClient, tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    repo_id = _register_and_index(client, tmp_path)

    list_response = client.get(f"/repositories/{repo_id}/files")
    assert list_response.status_code == 200
    assert "a.py" in list_response.json()

    detail_response = client.get(f"/repositories/{repo_id}/files/a.py")
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["content"] == "def f():\n    return 1\n"
    assert payload["symbols"][0]["name"] == "f"


def test_file_detail_rejects_path_traversal(client: TestClient, tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    repo_id = _register_and_index(client, tmp_path)

    response = client.get(f"/repositories/{repo_id}/files/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code in (400, 404)


def test_unknown_file_returns_404(client: TestClient, tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    repo_id = _register_and_index(client, tmp_path)

    response = client.get(f"/repositories/{repo_id}/files/does_not_exist.py")
    assert response.status_code == 404
