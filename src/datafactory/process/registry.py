"""Explicit processor registry. Add one line per new processor."""

from datafactory.core.errors import PluginNotFoundError
from datafactory.process.base import Processor
from datafactory.process.processors.select_columns import SelectColumns

PROCESSORS: dict[str, type[Processor]] = {
    SelectColumns.name: SelectColumns,
}


def get_processor(name: str) -> Processor:
    try:
        return PROCESSORS[name]()
    except KeyError:
        raise PluginNotFoundError(f"unknown processor {name!r}") from None
