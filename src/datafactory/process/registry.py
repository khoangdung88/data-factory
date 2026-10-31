"""Explicit processor and reader registries. Add one line per new plugin."""

from datafactory.core.errors import PluginNotFoundError
from datafactory.process.base import Processor, Reader
from datafactory.process.processors.drop_rows_missing import DropRowsMissing
from datafactory.process.processors.rename_columns import RenameColumns
from datafactory.process.processors.select_columns import SelectColumns
from datafactory.process.processors.sort_rows import SortRows
from datafactory.process.readers.csv_file import CsvFileReader
from datafactory.process.readers.json_records import JsonRecordsReader

PROCESSORS: dict[str, type[Processor]] = {
    SelectColumns.name: SelectColumns,
    RenameColumns.name: RenameColumns,
    DropRowsMissing.name: DropRowsMissing,
    SortRows.name: SortRows,
}

READERS: dict[str, type[Reader]] = {
    CsvFileReader.name: CsvFileReader,
    JsonRecordsReader.name: JsonRecordsReader,
}


def get_processor(name: str) -> Processor:
    try:
        return PROCESSORS[name]()
    except KeyError:
        raise PluginNotFoundError(f"unknown processor {name!r}") from None


def get_reader(name: str) -> Reader:
    try:
        return READERS[name]()
    except KeyError:
        raise PluginNotFoundError(f"unknown reader {name!r}") from None
