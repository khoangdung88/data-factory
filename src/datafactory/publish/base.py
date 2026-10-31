"""Publisher interface. A publisher distributes an already-built product package."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from datafactory.contracts.package import DataPackage
from datafactory.core.config import Settings


@dataclass(frozen=True)
class PublishContext:
    package_dir: Path
    package: DataPackage
    settings: Settings


class Publisher(ABC):
    name: ClassVar[str]
    version: ClassVar[str]
    remote: ClassVar[bool] = False
    """Remote publishers (network, marketplaces) only run with an explicit ``--release``."""

    @abstractmethod
    def publish(self, ctx: PublishContext, params: Mapping[str, Any]) -> str:
        """Publish the package; return where it went."""
