import pytest

from conftest import NOW
from datafactory.core.config import Settings
from datafactory.core.errors import ProductExistsError, QualityGateError
from datafactory.core.storage import Zone, batch_dir
from datafactory.pipeline.runner import Stage, load_dataset, run
from datafactory.publish.package import build_package


def _processed(settings: Settings) -> str:
    run("sample-csv", stage=Stage.COLLECT, settings=settings, now=NOW)
    return run("sample-csv", stage=Stage.PROCESS, settings=settings).batch_id


def test_quality_gate_blocks_publish(settings: Settings) -> None:
    batch_id = _processed(settings)
    spec, schema, ddir = load_dataset("sample-csv", settings)
    strict = spec.model_copy(
        update={"quality": spec.quality.model_copy(update={"max_invalid_ratio": 0.0})}
    )
    with pytest.raises(QualityGateError):
        build_package(strict, schema, batch_id, dataset_dir=ddir, settings=settings, now=NOW)


def test_republish_same_version_is_idempotent_but_different_data_fails(
    settings: Settings,
) -> None:
    batch_id = _processed(settings)
    spec, schema, ddir = load_dataset("sample-csv", settings)
    kw = {"dataset_dir": ddir, "settings": settings, "now": NOW}
    first, _ = build_package(spec, schema, batch_id, **kw)
    again, _ = build_package(spec, schema, batch_id, **kw)
    assert first == again

    data = batch_dir(settings, Zone.STAGED, "sample-csv", batch_id) / "data.csv"
    data.write_text(data.read_text() + "Z-9,x,y,1,USD,true,\n")
    with pytest.raises(ProductExistsError):
        build_package(spec, schema, batch_id, **kw)
