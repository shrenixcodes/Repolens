import json
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_ask_before_indexing_errors_helpfully(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["ask", "anything", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not been indexed" in result.output


def test_ask_with_no_evidence_is_honest(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def foo():\n    pass\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["ask", "zzzznonexistentzzzz", "--repo", str(tmp_path)])
    assert "couldn't determine this confidently" in result.output


def test_ask_with_evidence_cites_real_sources(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/auth.py",
        "def verify_jwt_token(token):\n    '''Verifies a JWT auth token.'''\n    return True\n",
    )
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["ask", "jwt token verification", "--repo", str(tmp_path)])
    assert "app/auth.py" in result.output
    assert "Sources:" in result.output


def test_ask_json_output(tmp_path: Path) -> None:
    _write(tmp_path, "app/auth.py", "def verify_jwt_token(token):\n    return True\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["ask", "jwt token", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["grounded"] is True
    assert payload["citations"][0]["path"] == "app/auth.py"


def test_ask_uses_mock_provider_by_default_offline(tmp_path: Path) -> None:
    _write(tmp_path, "app/auth.py", "def verify_jwt_token(token):\n    return True\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["ask", "jwt token", "--repo", str(tmp_path)])
    assert "No language model is configured" in result.output
