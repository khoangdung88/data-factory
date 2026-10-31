from pathlib import Path

import pytest
from typer.testing import CliRunner

from datafactory.cli import app
from datafactory.core.config import get_settings


def test_version_command_prints_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"


def test_run_command_reports_errors_with_exit_code_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DF_DATASETS_DIR", str(tmp_path))
    get_settings.cache_clear()
    result = CliRunner().invoke(app, ["run", "missing"])
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "not found" in result.output
