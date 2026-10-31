"""Raw zone contract: what a connector produced and where it came from."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    sha256: str
    bytes: int


class BatchManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset: str
    batch_id: str
    connector: str
    connector_version: str
    source: str
    license: str
    fetched_at: datetime
    files: list[FileEntry]
