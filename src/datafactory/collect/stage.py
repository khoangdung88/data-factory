"""Collect stage: run the dataset's connector and store an immutable raw batch."""

import hashlib
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from datafactory.collect.base import FetchContext
from datafactory.collect.registry import get_connector
from datafactory.contracts.batch import BatchManifest, FileEntry
from datafactory.contracts.dataset import DatasetSpec
from datafactory.core.config import Settings
from datafactory.core.errors import CollectError
from datafactory.core.logging import get_logger
from datafactory.core.storage import MANIFEST_FILE, Zone, sha256_file, write_text, zone_dir

log = get_logger(__name__)


def run_collect(
    spec: DatasetSpec, dataset_dir: Path, settings: Settings, now: datetime
) -> BatchManifest:
    connector = get_connector(spec.source.plugin)
    slug_dir = zone_dir(settings, Zone.RAW, spec.slug)
    slug_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-", dir=slug_dir))
    try:
        source = connector.fetch(spec.source.params, FetchContext(tmp, dataset_dir))
        files = [
            FileEntry(path=f.name, sha256=sha256_file(f), bytes=f.stat().st_size)
            for f in sorted(tmp.iterdir())
            if f.is_file()
        ]
        if not files:
            raise CollectError(f"{connector.name} produced no files")
        batch_id = _batch_id(connector.name, connector.version, spec.source.params, files)
        final = slug_dir / batch_id
        if final.exists():
            log.info("batch %s already collected, reusing it", batch_id)
            return BatchManifest.model_validate_json((final / MANIFEST_FILE).read_text("utf-8"))
        manifest = BatchManifest(
            dataset=spec.slug,
            batch_id=batch_id,
            connector=connector.name,
            connector_version=connector.version,
            source=source,
            license=spec.source.license,
            fetched_at=now,
            files=files,
        )
        write_text(tmp / MANIFEST_FILE, manifest.model_dump_json(indent=2) + "\n")
        tmp.rename(final)
        log.info("collected batch %s (%d files)", batch_id, len(files))
        return manifest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _batch_id(name: str, version: str, params: object, files: list[FileEntry]) -> str:
    key = json.dumps(
        {
            "connector": name,
            "version": version,
            "params": params,
            "files": [[f.path, f.sha256] for f in files],
        },
        sort_keys=True,
    )
    return hashlib.sha256(key.encode()).hexdigest()[:12]
