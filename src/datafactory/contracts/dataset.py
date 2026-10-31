"""Dataset definition (``datasets/<slug>/dataset.yaml``) and table schema (``schema/vN.json``)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StepSpec(_Strict):
    plugin: str
    params: dict[str, Any] = Field(default_factory=dict)


class SourceSpec(StepSpec):
    license: str = Field(min_length=1, description="Source license/terms allowing our use")


class License(_Strict):
    name: str
    path: str


class QualityGates(_Strict):
    min_rows: int = Field(default=1, ge=0)
    max_invalid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class DatasetSpec(_Strict):
    slug: str = Field(pattern=SLUG_PATTERN)
    title: str
    description: str
    version: str = Field(pattern=SEMVER_PATTERN)
    schema_version: int = Field(ge=1)
    license: License
    source: SourceSpec
    processing: list[StepSpec] = Field(default_factory=list)
    quality: QualityGates = QualityGates()
    publish: list[StepSpec] = Field(default_factory=list)
    pricing: dict[str, Any] | None = None


FieldType = Literal["string", "integer", "number", "boolean", "date"]


class FieldConstraints(_Strict):
    required: bool = False


class SchemaField(_Strict):
    name: str
    type: FieldType = "string"
    description: str = ""
    constraints: FieldConstraints = FieldConstraints()


class TableSchema(_Strict):
    """Subset of Frictionless Table Schema."""

    fields: list[SchemaField] = Field(min_length=1)

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]
