import json
import subprocess
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


def _init_repo_with_history(repo_root: Path) -> None:
    _git(repo_root, "init", "-q", "-b", "main")
    _git(repo_root, "config", "user.name", "Test User")
    _git(repo_root, "config", "user.email", "test@example.com")
    (repo_root / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    _git(repo_root, "add", "a.py")
    _git(repo_root, "commit", "-q", "-m", "Add foo")
    (repo_root / "a.py").write_text("def foo():\n    return 2\n", encoding="utf-8")
    _git(repo_root, "add", "a.py")
    _git(repo_root, "commit", "-q", "-m", "Fix foo to return 2")


def test_history_requires_git_repository(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["history", "a.py", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not a Git repository" in result.output


def test_history_shows_real_commits(tmp_path: Path) -> None:
    _init_repo_with_history(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["history", "a.py", "--repo", str(tmp_path)])
    assert "Fix foo to return 2" in result.output
    assert "Add foo" in result.output
    assert "Test User" in result.output


def test_history_json_output(tmp_path: Path) -> None:
    _init_repo_with_history(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["history", "a.py", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert len(payload) == 2
    assert payload[0]["subject"] == "Fix foo to return 2"


def test_history_empty_for_untracked_file(tmp_path: Path) -> None:
    _init_repo_with_history(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["history", "never_existed.py", "--repo", str(tmp_path)])
    assert "No commit history found" in result.output


def test_history_rejects_path_traversal(tmp_path: Path) -> None:
    _init_repo_with_history(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["history", "../outside.py", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "Invalid path" in result.output
