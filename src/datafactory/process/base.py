"""Processor interface. A processor is a pure, deterministic Table -> Table step."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar

from datafactory.contracts.table import Table


class Processor(ABC):
    name: ClassVar[str]
    version: ClassVar[str]

    @abstractmethod
    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        """Return a new table; never mutate the input."""
