"""In-memory table passed between processors. Values stay strings until schema validation."""

from pydantic import BaseModel, ConfigDict


class Table(BaseModel):
    model_config = ConfigDict(frozen=True)

    columns: list[str]
    rows: list[list[str]]
