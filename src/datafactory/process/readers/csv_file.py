"""Read the single CSV file of a raw batch."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Reader
from datafactory.process.csvio import read_csv


class CsvFileReader(Reader):
    name = "csv"
    version = "1.0.0"

    def read(self, raw_dir: Path, files: list[str], params: Mapping[str, Any]) -> Table:
        if params:
            raise ConfigError(f"csv reader takes no params, got {sorted(params)}")
        csv_files = [f for f in files if f.endswith(".csv")]
        if len(csv_files) != 1:
            raise ConfigError(f"expected exactly one CSV in raw batch, found {csv_files}")
        return read_csv(raw_dir / csv_files[0])
