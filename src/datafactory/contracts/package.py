"""Products zone contract: a Frictionless Data Package descriptor (``datapackage.json``)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from datafactory.contracts.dataset import TableSchema
from datafactory.contracts.staged import PluginRef, QualityReport


class PackageLicense(BaseModel):
    name: str
    path: str


class PackageSource(BaseModel):
    title: str
    path: str


class Resource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    path: str
    format: str = "csv"
    mediatype: str = "text/csv"
    encoding: str = "utf-8"
    bytes: int
    hash: str
    table_schema: TableSchema = Field(alias="schema")


class Lineage(BaseModel):
    batch_ids: list[str]
    connector: PluginRef
    processors: list[PluginRef]


class DataPackage(BaseModel):
    name: str
    title: str
    description: str
    version: str
    created: datetime
    licenses: list[PackageLicense]
    sources: list[PackageSource]
    resources: list[Resource]
    lineage: Lineage
    quality: QualityReport

    def to_json(self) -> str:
        return self.model_dump_json(indent=2, by_alias=True) + "\n"
