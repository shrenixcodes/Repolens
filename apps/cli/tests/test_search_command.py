import json
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_search_before_indexing_errors_helpfully(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "anything", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not been indexed" in result.output


def test_search_finds_indexed_function(tmp_path: Path) -> None:
    _write(tmp_path, "auth.py", "def verify_jwt_token(token):\n    return True\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["search", "jwt token", "--repo", str(tmp_path)])
    assert "auth.py" in result.output
    assert "verify_jwt_token" in result.output


def test_search_json_output(tmp_path: Path) -> None:
    _write(tmp_path, "auth.py", "def verify_jwt_token(token):\n    return True\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["search", "jwt", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload[0]["file_path"] == "auth.py"


def test_search_no_matches(tmp_path: Path) -> None:
    _write(tmp_path, "auth.py", "def login():\n    pass\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["search", "zzzznonexistentzzzz", "--repo", str(tmp_path)])
    assert "No matches" in result.output
