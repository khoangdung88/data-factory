import pytest

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.processors.drop_rows_missing import DropRowsMissing
from datafactory.process.processors.rename_columns import RenameColumns
from datafactory.process.processors.sort_rows import SortRows

TABLE = Table(columns=["k", "v"], rows=[["b", "2"], ["a", ""], ["a", "1"]])


def test_drop_rows_missing() -> None:
    out = DropRowsMissing().apply(TABLE, {"columns": ["v"]})
    assert out.rows == [["b", "2"], ["a", "1"]]
    assert len(TABLE.rows) == 3


def test_rename_columns() -> None:
    out = RenameColumns().apply(TABLE, {"mapping": {"k": "key"}})
    assert out.columns == ["key", "v"]
    with pytest.raises(ConfigError, match="duplicate"):
        RenameColumns().apply(TABLE, {"mapping": {"k": "v"}})


def test_sort_rows_is_stable() -> None:
    out = SortRows().apply(TABLE, {"by": ["k"]})
    assert out.rows == [["a", ""], ["a", "1"], ["b", "2"]]


@pytest.mark.parametrize(
    ("processor", "params"),
    [
        (DropRowsMissing(), {"columns": ["z"]}),
        (RenameColumns(), {"mapping": {"z": "y"}}),
        (SortRows(), {"by": ["z"]}),
    ],
)
def test_unknown_column_is_config_error(processor: object, params: dict[str, object]) -> None:
    with pytest.raises(ConfigError, match="unknown columns"):
        processor.apply(TABLE, params)  # type: ignore[attr-defined]
