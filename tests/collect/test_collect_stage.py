from pathlib import Path

import pytest

from conftest import NOW
from datafactory.collect.stage import run_collect
from datafactory.contracts.dataset import DatasetSpec
from datafactory.core.config import Settings
from datafactory.core.errors import ConfigError, PluginNotFoundError
from datafactory.core.storage import MANIFEST_FILE, Zone, zone_dir


def _spec(path: str, plugin: str = "local_file") -> DatasetSpec:
    return DatasetSpec.model_validate(
        {
            "slug": "demo",
            "title": "t",
            "description": "d",
            "version": "1.0.0",
            "schema_version": 1,
            "license": {"name": "CC0-1.0", "path": "x"},
            "source": {"plugin": plugin, "license": "CC0-1.0", "params": {"path": path}},
        }
    )


def test_collect_writes_manifest_and_is_idempotent(tmp_path: Path, settings: Settings) -> None:
    (tmp_path / "a.csv").write_text("x\n1\n")
    first = run_collect(_spec("a.csv"), tmp_path, settings, NOW)
    second = run_collect(_spec("a.csv"), tmp_path, settings, NOW)

    assert first == second
    batches = [p for p in zone_dir(settings, Zone.RAW, "demo").iterdir()]
    assert [p.name for p in batches] == [first.batch_id]
    assert (batches[0] / MANIFEST_FILE).is_file()
    assert first.files[0].path == "a.csv"
    assert first.license == "CC0-1.0"


def test_changed_source_gives_new_batch(tmp_path: Path, settings: Settings) -> None:
    src = tmp_path / "a.csv"
    src.write_text("x\n1\n")
    first = run_collect(_spec("a.csv"), tmp_path, settings, NOW)
    src.write_text("x\n2\n")
    assert run_collect(_spec("a.csv"), tmp_path, settings, NOW).batch_id != first.batch_id


def test_missing_file_and_unknown_connector(tmp_path: Path, settings: Settings) -> None:
    with pytest.raises(ConfigError):
        run_collect(_spec("nope.csv"), tmp_path, settings, NOW)
    with pytest.raises(PluginNotFoundError):
        run_collect(_spec("a.csv", plugin="nope"), tmp_path, settings, NOW)
    assert not any(zone_dir(settings, Zone.RAW, "demo").iterdir())
