"""Drop rows where any of the listed columns is empty (e.g. observations without a value)."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Processor


class DropRowsMissingParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[str] = Field(min_length=1)


class DropRowsMissing(Processor):
    name = "drop_rows_missing"
    version = "1.0.0"

    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        p = DropRowsMissingParams.model_validate(params)
        missing = [c for c in p.columns if c not in table.columns]
        if missing:
            raise ConfigError(f"drop_rows_missing: unknown columns {missing}")
        idx = [table.columns.index(c) for c in p.columns]
        rows = [row for row in table.rows if all(row[i] != "" for i in idx)]
        return Table(columns=table.columns, rows=rows)
