"""Data zone layout: ``<data_dir>/<zone>/<slug>/<batch_id|version>/``."""

import hashlib
from enum import StrEnum
from pathlib import Path

from datafactory.core.config import Settings

MANIFEST_FILE = "_manifest.json"


class Zone(StrEnum):
    RAW = "raw"
    STAGED = "staged"
    PRODUCTS = "products"


def zone_dir(settings: Settings, zone: Zone, slug: str) -> Path:
    return settings.data_dir / zone.value / slug


def batch_dir(settings: Settings, zone: Zone, slug: str, batch_id: str) -> Path:
    return zone_dir(settings, zone, slug) / batch_id


def product_dir(settings: Settings, slug: str, version: str) -> Path:
    return zone_dir(settings, Zone.PRODUCTS, slug) / version


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with ``\\n`` line endings on every OS (byte-stable outputs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
