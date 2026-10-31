"""Processor interface. A processor is a pure, deterministic Table -> Table step."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

from datafactory.contracts.table import Table


class Processor(ABC):
    name: ClassVar[str]
    version: ClassVar[str]

    @abstractmethod
    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        """Return a new table; never mutate the input."""


class Reader(ABC):
    """Turn the files of a raw batch into one table (all values as strings)."""

    name: ClassVar[str]
    version: ClassVar[str]

    @abstractmethod
    def read(self, raw_dir: Path, files: list[str], params: Mapping[str, Any]) -> Table:
        """Read ``files`` (paths relative to ``raw_dir``, sorted) without modifying them."""
