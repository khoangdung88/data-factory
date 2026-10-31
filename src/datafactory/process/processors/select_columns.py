"""Keep only the listed columns, in the listed order."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Processor


class SelectColumnsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[str] = Field(min_length=1)


class SelectColumns(Processor):
    name = "select_columns"
    version = "1.0.0"

    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        p = SelectColumnsParams.model_validate(params)
        missing = [c for c in p.columns if c not in table.columns]
        if missing:
            raise ConfigError(f"select_columns: unknown columns {missing}")
        idx = [table.columns.index(c) for c in p.columns]
        return Table(columns=list(p.columns), rows=[[row[i] for i in idx] for row in table.rows])
