import json
from pathlib import Path

from click.testing import CliRunner

from repolens_cli.main import cli


def test_help_lists_doctor_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "doctor" in result.output


def test_version_flag_prints_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "repolens" in result.output.lower()


def test_doctor_runs_against_a_real_directory(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--repo", str(tmp_path)])
    assert "python" in result.output.lower()
    assert "sqlite" in result.output.lower()


def test_doctor_json_output_is_valid_json(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--repo", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    names = {entry["name"] for entry in payload}
    assert {"python", "git", "sqlite", "cache_dir", "config"} <= names


def test_doctor_exits_nonzero_on_failure(tmp_path: Path, monkeypatch) -> None:
    from repolens_cli import main as main_module
    from repolens_cli.doctor import CheckResult

    def _fake_checks(repo_root: Path) -> list[CheckResult]:
        return [CheckResult("fake", "fail", "forced failure for test")]

    monkeypatch.setattr(main_module, "run_checks", _fake_checks)
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--repo", str(tmp_path)])
    assert result.exit_code == 1
