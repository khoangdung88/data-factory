"""Every dataset: recorded raw batch (fixtures/input) -> process -> publish == fixtures/expected."""

import shutil
from pathlib import Path

import pytest

from conftest import DATASETS_DIR, NOW
from datafactory.contracts.batch import BatchManifest
from datafactory.core.config import Settings
from datafactory.core.storage import MANIFEST_FILE, Zone, batch_dir
from datafactory.pipeline.runner import Stage, run

DATASETS = sorted(p.parent.name for p in DATASETS_DIR.glob("*/dataset.yaml"))


def _files(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("slug", DATASETS)
def test_dataset_matches_golden_output(slug: str, settings: Settings) -> None:
    fixtures = DATASETS_DIR / slug / "fixtures"
    batch = BatchManifest.model_validate_json((fixtures / "input" / MANIFEST_FILE).read_text())
    shutil.copytree(fixtures / "input", batch_dir(settings, Zone.RAW, slug, batch.batch_id))

    run(slug, stage=Stage.PROCESS, batch_id=batch.batch_id, settings=settings)
    result = run(slug, stage=Stage.PUBLISH, batch_id=batch.batch_id, settings=settings, now=NOW)

    assert result.package_dir is not None
    assert _files(result.package_dir) == _files(fixtures / "expected")


def test_every_dataset_has_golden_fixtures() -> None:
    assert DATASETS, "no datasets found"
    for slug in DATASETS:
        fixtures = DATASETS_DIR / slug / "fixtures"
        assert (fixtures / "input" / MANIFEST_FILE).is_file(), slug
        assert (fixtures / "expected" / "datapackage.json").is_file(), slug
