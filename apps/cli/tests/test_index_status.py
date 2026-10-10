import json
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_init_writes_default_config(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "repolens.yaml").exists()
    assert (tmp_path / ".repolens").is_dir()


def test_init_does_not_overwrite_existing_config(tmp_path: Path) -> None:
    (tmp_path / "repolens.yaml").write_text("llm:\n  provider: ollama\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--repo", str(tmp_path)])
    assert "already exists" in result.output
    assert "ollama" in (tmp_path / "repolens.yaml").read_text(encoding="utf-8")


def test_index_command_reports_counts(tmp_path: Path) -> None:
    _write(tmp_path, "app.py", "def f():\n    return 1\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "1 indexed" in result.output


def test_index_command_json_output(tmp_path: Path) -> None:
    _write(tmp_path, "app.py", "def f():\n    return 1\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["files_indexed"] == 1


def test_status_before_indexing_errors_helpfully(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "not been indexed" in result.output


def test_status_after_indexing_reports_counts(tmp_path: Path) -> None:
    _write(tmp_path, "app.py", "def f():\n    return 1\n")
    runner = CliRunner()
    runner.invoke(cli, ["index", "--repo", str(tmp_path)])
    result = runner.invoke(cli, ["status", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["total_files"] == 1
    assert payload["files_by_language"]["python"] == 1
