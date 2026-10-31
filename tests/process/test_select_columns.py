import pytest

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.processors.select_columns import SelectColumns

TABLE = Table(columns=["a", "b", "c"], rows=[["1", "2", "3"]])


def test_selects_and_reorders_without_mutating_input() -> None:
    out = SelectColumns().apply(TABLE, {"columns": ["c", "a"]})
    assert out == Table(columns=["c", "a"], rows=[["3", "1"]])
    assert TABLE.columns == ["a", "b", "c"]


def test_unknown_column_is_config_error() -> None:
    with pytest.raises(ConfigError):
        SelectColumns().apply(TABLE, {"columns": ["z"]})
