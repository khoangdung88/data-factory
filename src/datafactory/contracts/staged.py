"""Staged zone contract: processed data plus quality metrics."""

from pydantic import BaseModel, ConfigDict


class PluginRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str


class QualityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    rows_in: int
    rows_valid: int
    rows_invalid: int
    null_counts: dict[str, int]

    @property
    def invalid_ratio(self) -> float:
        return self.rows_invalid / self.rows_in if self.rows_in else 0.0


class StagedManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset: str
    batch_id: str
    schema_version: int
    processors: list[PluginRef]
    quality: QualityReport
    data_file: str = "data.csv"
    quarantine_file: str = "quarantine.csv"
