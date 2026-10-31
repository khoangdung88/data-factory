"""Rename columns; unlisted columns keep their names."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Processor


class RenameColumnsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mapping: dict[str, str] = Field(min_length=1)


class RenameColumns(Processor):
    name = "rename_columns"
    version = "1.0.0"

    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        p = RenameColumnsParams.model_validate(params)
        missing = [c for c in p.mapping if c not in table.columns]
        if missing:
            raise ConfigError(f"rename_columns: unknown columns {missing}")
        columns = [p.mapping.get(c, c) for c in table.columns]
        if len(set(columns)) != len(columns):
            raise ConfigError(f"rename_columns: duplicate column names {columns}")
        return Table(columns=columns, rows=table.rows)
