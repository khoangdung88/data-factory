from pathlib import Path

import pytest

from conftest import NOW
from datafactory.core.config import Settings
from datafactory.core.errors import BatchNotFoundError, ConfigError
from datafactory.pipeline.runner import Stage, latest_batch, run


def test_full_run_produces_package(settings: Settings) -> None:
    result = run("sample-csv", settings=settings, now=NOW)
    assert result.package_dir == settings.data_dir / "products" / "sample-csv" / "1.0.0"
    assert (result.package_dir / "datapackage.json").is_file()


def test_each_stage_runs_alone_from_previous_zone(settings: Settings) -> None:
    collected = run("sample-csv", stage=Stage.COLLECT, settings=settings, now=NOW)
    assert collected.package_dir is None
    assert latest_batch("sample-csv", settings) == collected.batch_id

    processed = run("sample-csv", stage=Stage.PROCESS, settings=settings)
    assert processed.batch_id == collected.batch_id

    published = run("sample-csv", stage=Stage.PUBLISH, settings=settings, now=NOW)
    assert published.package_dir is not None


def test_stage_without_previous_zone_fails(settings: Settings) -> None:
    with pytest.raises(BatchNotFoundError):
        run("sample-csv", stage=Stage.PROCESS, settings=settings)
    with pytest.raises(BatchNotFoundError):
        run("sample-csv", stage=Stage.PUBLISH, batch_id="missing", settings=settings)


def test_unknown_or_invalid_dataset(tmp_path: Path) -> None:
    ds = tmp_path / "datasets"
    (ds / "bad").mkdir(parents=True)
    (ds / "bad" / "dataset.yaml").write_text("slug: bad\n")
    s = Settings(data_dir=tmp_path / "data", datasets_dir=ds)
    with pytest.raises(ConfigError, match="not found"):
        run("nope", settings=s)
    with pytest.raises(ConfigError, match="invalid dataset"):
        run("bad", settings=s)
