"""Load a dataset definition and run its stages."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import ValidationError

from datafactory.collect.stage import run_collect
from datafactory.contracts.batch import BatchManifest
from datafactory.contracts.dataset import DatasetSpec, TableSchema
from datafactory.core.config import Settings, get_settings
from datafactory.core.errors import BatchNotFoundError, ConfigError
from datafactory.core.storage import MANIFEST_FILE, Zone, zone_dir
from datafactory.process.stage import run_process
from datafactory.publish.stage import run_publish


class Stage(StrEnum):
    COLLECT = "collect"
    PROCESS = "process"
    PUBLISH = "publish"


@dataclass
class RunResult:
    batch_id: str
    package_dir: Path | None = None
    destinations: list[str] = field(default_factory=list)


def load_dataset(slug: str, settings: Settings) -> tuple[DatasetSpec, TableSchema, Path]:
    dataset_dir = settings.datasets_dir / slug
    spec_file = dataset_dir / "dataset.yaml"
    if not spec_file.is_file():
        raise ConfigError(f"dataset {slug!r} not found ({spec_file})")
    try:
        spec = DatasetSpec.model_validate(yaml.safe_load(spec_file.read_text("utf-8")))
        schema_file = dataset_dir / "schema" / f"v{spec.schema_version}.json"
        schema = TableSchema.model_validate_json(schema_file.read_text("utf-8"))
    except (ValidationError, OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"invalid dataset {slug!r}: {exc}") from exc
    if spec.slug != slug:
        raise ConfigError(f"dataset.yaml slug {spec.slug!r} != folder name {slug!r}")
    return spec, schema, dataset_dir


def latest_batch(slug: str, settings: Settings) -> str:
    manifests = [
        BatchManifest.model_validate_json(p.read_text("utf-8"))
        for p in zone_dir(settings, Zone.RAW, slug).glob(f"*/{MANIFEST_FILE}")
    ]
    if not manifests:
        raise BatchNotFoundError(f"no raw batch for {slug!r}; run the collect stage first")
    return max(manifests, key=lambda m: (m.fetched_at, m.batch_id)).batch_id


def run(
    slug: str,
    *,
    stage: Stage | None = None,
    batch_id: str | None = None,
    release: bool = False,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> RunResult:
    """Run all stages, or only ``stage`` (reading the previous zone)."""
    settings = settings or get_settings()
    now = now or datetime.now(UTC).replace(microsecond=0)
    spec, schema, dataset_dir = load_dataset(slug, settings)
    stages = list(Stage) if stage is None else [stage]

    if Stage.COLLECT in stages:
        batch_id = run_collect(spec, dataset_dir, settings, now).batch_id
    batch_id = batch_id or latest_batch(slug, settings)
    result = RunResult(batch_id=batch_id)
    if Stage.PROCESS in stages:
        run_process(spec, schema, batch_id, settings)
    if Stage.PUBLISH in stages:
        published = run_publish(
            spec,
            schema,
            batch_id,
            dataset_dir=dataset_dir,
            settings=settings,
            now=now,
            release=release,
        )
        result.package_dir = published.package_dir
        result.destinations = published.destinations
    return result
