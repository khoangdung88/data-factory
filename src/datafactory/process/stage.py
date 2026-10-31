"""Process stage: raw batch -> processor steps -> schema validation -> staged batch."""

from datafactory.contracts.batch import BatchManifest
from datafactory.contracts.dataset import DatasetSpec, TableSchema
from datafactory.contracts.staged import PluginRef, StagedManifest
from datafactory.core.config import Settings
from datafactory.core.errors import BatchNotFoundError, ConfigError
from datafactory.core.logging import get_logger
from datafactory.core.storage import MANIFEST_FILE, Zone, batch_dir, write_text
from datafactory.process.csvio import read_csv, write_csv
from datafactory.process.registry import get_processor
from datafactory.process.validate import validate

log = get_logger(__name__)


def run_process(
    spec: DatasetSpec, schema: TableSchema, batch_id: str, settings: Settings
) -> StagedManifest:
    raw = batch_dir(settings, Zone.RAW, spec.slug, batch_id)
    if not (raw / MANIFEST_FILE).is_file():
        raise BatchNotFoundError(f"raw batch {batch_id} not found for {spec.slug}")
    batch = BatchManifest.model_validate_json((raw / MANIFEST_FILE).read_text("utf-8"))
    csv_files = [f.path for f in batch.files if f.path.endswith(".csv")]
    if len(csv_files) != 1:
        raise ConfigError(f"expected exactly one CSV in raw batch, found {csv_files}")

    table = read_csv(raw / csv_files[0])
    applied: list[PluginRef] = []
    for step in spec.processing:
        processor = get_processor(step.plugin)
        table = processor.apply(table, step.params)
        applied.append(PluginRef(name=processor.name, version=processor.version))
    valid, quarantine, quality = validate(table, schema)

    staged = StagedManifest(
        dataset=spec.slug,
        batch_id=batch_id,
        schema_version=spec.schema_version,
        processors=applied,
        quality=quality,
    )
    out = batch_dir(settings, Zone.STAGED, spec.slug, batch_id)
    write_csv(out / staged.data_file, valid.columns, valid.rows)
    write_csv(out / staged.quarantine_file, [*valid.columns, "_error"], quarantine)
    write_text(out / MANIFEST_FILE, staged.model_dump_json(indent=2) + "\n")
    log.info(
        "processed %s: %d valid, %d quarantined", batch_id, quality.rows_valid, quality.rows_invalid
    )
    return staged
