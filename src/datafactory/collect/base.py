"""Connector interface. A connector copies source data as-is into a raw batch directory."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar


@dataclass(frozen=True)
class FetchContext:
    dest: Path
    dataset_dir: Path


class Connector(ABC):
    name: ClassVar[str]
    version: ClassVar[str]

    @abstractmethod
    def fetch(self, params: Mapping[str, Any], ctx: FetchContext) -> str:
        """Write raw files into ``ctx.dest``; return a stable description of the source."""
