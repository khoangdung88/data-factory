"""Read-only views of datasets and data zones for the UI."""

import csv
import re
import tempfile
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from datafactory.contracts.batch import BatchManifest
from datafactory.contracts.dataset import SLUG_PATTERN, DatasetSpec, TableSchema
from datafactory.contracts.package import DataPackage
from datafactory.contracts.staged import StagedManifest
from datafactory.core.config import Settings
from datafactory.core.errors import ConfigError
from datafactory.core.storage import MANIFEST_FILE, Zone, zone_dir
from datafactory.pipeline.runner import load_dataset

PACKAGE_FILE = "datapackage.json"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class NotFoundError(LookupError):
    """Unknown dataset, batch or product (also for unsafe names)."""


@dataclass(frozen=True)
class DatasetEntry:
    slug: str
    spec: DatasetSpec | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchEntry:
    raw: BatchManifest
    staged: StagedManifest | None


@dataclass(frozen=True)
class Preview:
    columns: list[str]
    rows: list[list[str]]
    truncated: bool


def check_slug(slug: str) -> str:
    if not re.fullmatch(SLUG_PATTERN, slug):
        raise NotFoundError(slug)
    return slug


def safe_name(name: str) -> str:
    """A single path segment that cannot traverse outside the data zones."""
    if not _NAME.fullmatch(name) or ".." in name:
        raise NotFoundError(name)
    return name


def _child(parent: Path, name: str) -> Path:
    return parent / safe_name(name)


def list_datasets(settings: Settings) -> list[DatasetEntry]:
    root = settings.datasets_dir
    if not root.is_dir():
        return []
    entries = []
    for spec_file in sorted(root.glob("*/dataset.yaml")):
        slug = spec_file.parent.name
        try:
            spec, _, _ = load_dataset(slug, settings)
        except ConfigError as exc:
            entries.append(DatasetEntry(slug=slug, error=str(exc)))
        else:
            entries.append(DatasetEntry(slug=slug, spec=spec))
    return entries


def get_dataset(slug: str, settings: Settings) -> tuple[DatasetSpec, TableSchema]:
    check_slug(slug)
    if not (settings.datasets_dir / slug / "dataset.yaml").is_file():
        raise NotFoundError(slug)
    spec, schema, _ = load_dataset(slug, settings)
    return spec, schema


def list_batches(slug: str, settings: Settings) -> list[BatchEntry]:
    raw_root = zone_dir(settings, Zone.RAW, check_slug(slug))
    entries = []
    for manifest in raw_root.glob(f"*/{MANIFEST_FILE}"):
        try:
            raw = BatchManifest.model_validate_json(manifest.read_text("utf-8"))
        except (ValidationError, OSError):
            continue
        entries.append(BatchEntry(raw=raw, staged=_staged(slug, raw.batch_id, settings)))
    return sorted(entries, key=lambda e: (e.raw.fetched_at, e.raw.batch_id), reverse=True)


def get_batch(slug: str, batch_id: str, settings: Settings) -> BatchEntry:
    raw_dir = _child(zone_dir(settings, Zone.RAW, check_slug(slug)), batch_id)
    manifest = raw_dir / MANIFEST_FILE
    if not manifest.is_file():
        raise NotFoundError(batch_id)
    raw = BatchManifest.model_validate_json(manifest.read_text("utf-8"))
    return BatchEntry(raw=raw, staged=_staged(slug, batch_id, settings))


def staged_dir(slug: str, batch_id: str, settings: Settings) -> Path:
    return _child(zone_dir(settings, Zone.STAGED, check_slug(slug)), batch_id)


def _staged(slug: str, batch_id: str, settings: Settings) -> StagedManifest | None:
    manifest = staged_dir(slug, batch_id, settings) / MANIFEST_FILE
    if not manifest.is_file():
        return None
    try:
        return StagedManifest.model_validate_json(manifest.read_text("utf-8"))
    except (ValidationError, OSError):
        return None


def list_products(slug: str, settings: Settings) -> list[DataPackage]:
    root = zone_dir(settings, Zone.PRODUCTS, check_slug(slug))
    packages = []
    for descriptor in root.glob(f"*/{PACKAGE_FILE}"):
        try:
            packages.append(DataPackage.model_validate_json(descriptor.read_text("utf-8")))
        except (ValidationError, OSError):
            continue
    return sorted(packages, key=lambda p: p.created, reverse=True)


def product_dir(slug: str, version: str, settings: Settings) -> Path:
    path = _child(zone_dir(settings, Zone.PRODUCTS, check_slug(slug)), version)
    if not (path / PACKAGE_FILE).is_file():
        raise NotFoundError(version)
    return path


def get_product(slug: str, version: str, settings: Settings) -> DataPackage:
    descriptor = product_dir(slug, version, settings) / PACKAGE_FILE
    return DataPackage.model_validate_json(descriptor.read_text("utf-8"))


def preview_csv(path: Path, limit: int = 50) -> Preview | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        columns = next(reader, [])
        rows: list[list[str]] = []
        for row in reader:
            if len(rows) == limit:
                return Preview(columns=columns, rows=rows, truncated=True)
            rows.append(row)
    return Preview(columns=columns, rows=rows, truncated=False)


def zip_product(slug: str, version: str, settings: Settings) -> Iterator[bytes]:
    """Stream the product zip in chunks; the whole product is never loaded at once."""
    root = product_dir(slug, version, settings)
    prefix = f"{slug}-{version}/"
    files = sorted(p for p in root.rglob("*") if p.is_file())
    with tempfile.TemporaryFile(prefix="dfui-") as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in files:
                zf.write(path, prefix + path.relative_to(root).as_posix())
        tmp.seek(0)
        while chunk := tmp.read(1 << 16):
            yield chunk
