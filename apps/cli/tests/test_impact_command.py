import json
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_impact_before_indexing_errors_helpfully(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["impact", "a.py", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not been indexed" in result.output


def test_impact_unknown_target(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def f():\n    return 1\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["impact", "does_not_exist.py", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_impact_reports_direct_dependents(tmp_path: Path) -> None:
    _write(tmp_path, "utils.py", "def helper():\n    return 1\n")
    _write(tmp_path, "service.py", "from .utils import helper\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["impact", "utils.py", "--repo", str(tmp_path)])
    assert "service.py" in result.output
    assert "Limitations:" in result.output


def test_impact_json_output(tmp_path: Path) -> None:
    _write(tmp_path, "utils.py", "def helper():\n    return 1\n")
    _write(tmp_path, "service.py", "from .utils import helper\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["impact", "utils.py", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["target_found"] is True
    assert "service.py" in payload["direct_dependents"]


def test_impact_finds_related_tests(tmp_path: Path) -> None:
    _write(tmp_path, "app/service.py", "def process():\n    return 1\n")
    _write(
        tmp_path,
        "tests/test_service.py",
        "from app.service import process\n\ndef test_process():\n    assert process() == 1\n",
    )
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["impact", "app/service.py", "--repo", str(tmp_path)])
    assert "tests/test_service.py" in result.output
