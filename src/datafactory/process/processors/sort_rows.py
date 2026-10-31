"""Sort rows by the listed columns (text order, stable) for deterministic output."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Processor


class SortRowsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    by: list[str] = Field(min_length=1)


class SortRows(Processor):
    name = "sort_rows"
    version = "1.0.0"

    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        p = SortRowsParams.model_validate(params)
        missing = [c for c in p.by if c not in table.columns]
        if missing:
            raise ConfigError(f"sort_rows: unknown columns {missing}")
        idx = [table.columns.index(c) for c in p.by]
        rows = sorted(table.rows, key=lambda row: [row[i] for i in idx])
        return Table(columns=table.columns, rows=rows)
