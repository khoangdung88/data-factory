"""Publish stage: build the package, then run the dataset's publishers."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from datafactory.contracts.dataset import DatasetSpec, TableSchema
from datafactory.core.config import Settings
from datafactory.core.logging import get_logger
from datafactory.publish.base import PublishContext
from datafactory.publish.package import build_package
from datafactory.publish.registry import get_publisher

log = get_logger(__name__)


@dataclass(frozen=True)
class PublishResult:
    package_dir: Path
    destinations: list[str]


def run_publish(
    spec: DatasetSpec,
    schema: TableSchema,
    batch_id: str,
    *,
    dataset_dir: Path,
    settings: Settings,
    now: datetime,
    release: bool = False,
) -> PublishResult:
    package_dir, package = build_package(
        spec, schema, batch_id, dataset_dir=dataset_dir, settings=settings, now=now
    )
    ctx = PublishContext(package_dir=package_dir, package=package, settings=settings)
    destinations: list[str] = []
    for step in spec.publish:
        publisher = get_publisher(step.plugin)
        if publisher.remote and not release:
            log.info("dry-run: skipping remote publisher %s (use --release)", publisher.name)
            continue
        destinations.append(publisher.publish(ctx, step.params))
    return PublishResult(package_dir=package_dir, destinations=destinations)
