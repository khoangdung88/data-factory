"""Build the immutable product package in ``products/<slug>/<version>/``."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from datafactory.contracts.batch import BatchManifest
from datafactory.contracts.dataset import DatasetSpec, TableSchema
from datafactory.contracts.package import (
    DataPackage,
    Lineage,
    PackageLicense,
    PackageSource,
    Resource,
)
from datafactory.contracts.staged import PluginRef, StagedManifest
from datafactory.core.config import Settings
from datafactory.core.errors import (
    BatchNotFoundError,
    ConfigError,
    ProductExistsError,
    QualityGateError,
)
from datafactory.core.logging import get_logger
from datafactory.core.storage import (
    MANIFEST_FILE,
    Zone,
    batch_dir,
    product_dir,
    sha256_file,
    write_text,
)

log = get_logger(__name__)
PACKAGE_FILE = "datapackage.json"


def build_package(
    spec: DatasetSpec,
    schema: TableSchema,
    batch_id: str,
    *,
    dataset_dir: Path,
    settings: Settings,
    now: datetime,
) -> tuple[Path, DataPackage]:
    staged_dir = batch_dir(settings, Zone.STAGED, spec.slug, batch_id)
    raw_manifest = batch_dir(settings, Zone.RAW, spec.slug, batch_id) / MANIFEST_FILE
    if not (staged_dir / MANIFEST_FILE).is_file() or not raw_manifest.is_file():
        raise BatchNotFoundError(f"batch {batch_id} of {spec.slug} is not processed yet")
    staged = StagedManifest.model_validate_json((staged_dir / MANIFEST_FILE).read_text("utf-8"))
    batch = BatchManifest.model_validate_json(raw_manifest.read_text("utf-8"))
    _check_quality(spec, staged)
    datasheet = dataset_dir / "README.md"
    if not datasheet.is_file():
        raise ConfigError(f"{spec.slug}: datasheet README.md is required to publish")

    data_file = staged_dir / staged.data_file
    data_hash = f"sha256:{sha256_file(data_file)}"
    target = product_dir(settings, spec.slug, spec.version)
    if target.exists():
        existing = DataPackage.model_validate_json((target / PACKAGE_FILE).read_text("utf-8"))
        if existing.resources[0].hash == data_hash:
            log.info("%s %s already published with identical data", spec.slug, spec.version)
            return target, existing
        raise ProductExistsError(
            f"{spec.slug} {spec.version} exists with different data; bump `version`"
        )

    package = DataPackage(
        name=spec.slug,
        title=spec.title,
        description=spec.description,
        version=spec.version,
        created=now,
        licenses=[PackageLicense(name=spec.license.name, path=spec.license.path)],
        sources=[PackageSource(title=f"{batch.connector}: {batch.source}", path=batch.source)],
        resources=[
            Resource(
                name=spec.slug,
                path="data.csv",
                bytes=data_file.stat().st_size,
                hash=data_hash,
                table_schema=schema,
            )
        ],
        lineage=Lineage(
            batch_ids=[batch_id],
            connector=PluginRef(name=batch.connector, version=batch.connector_version),
            processors=staged.processors,
        ),
        quality=staged.quality,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-", dir=target.parent))
    try:
        shutil.copyfile(data_file, tmp / "data.csv")
        shutil.copyfile(datasheet, tmp / "README.md")
        write_text(tmp / "LICENSE", f"{spec.license.name}\n{spec.license.path}\n")
        write_text(tmp / PACKAGE_FILE, package.to_json())
        tmp.rename(target)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log.info("built package %s", target)
    return target, package


def _check_quality(spec: DatasetSpec, staged: StagedManifest) -> None:
    q, gates = staged.quality, spec.quality
    if q.rows_valid < gates.min_rows:
        raise QualityGateError(f"{q.rows_valid} valid rows < min_rows {gates.min_rows}")
    if q.invalid_ratio > gates.max_invalid_ratio:
        raise QualityGateError(
            f"invalid ratio {q.invalid_ratio:.2%} > max {gates.max_invalid_ratio:.2%}"
        )
