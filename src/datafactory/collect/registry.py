"""Explicit connector registry. Add one line per new connector."""

from datafactory.collect.base import Connector
from datafactory.collect.connectors.local_file import LocalFileConnector
from datafactory.collect.connectors.worldbank import WorldBankConnector
from datafactory.core.errors import PluginNotFoundError

CONNECTORS: dict[str, type[Connector]] = {
    LocalFileConnector.name: LocalFileConnector,
    WorldBankConnector.name: WorldBankConnector,
}


def get_connector(name: str) -> Connector:
    try:
        return CONNECTORS[name]()
    except KeyError:
        raise PluginNotFoundError(f"unknown connector {name!r}") from None
