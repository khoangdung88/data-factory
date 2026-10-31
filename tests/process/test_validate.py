import pytest

from datafactory.contracts.dataset import TableSchema
from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.validate import validate

SCHEMA = TableSchema.model_validate(
    {
        "fields": [
            {"name": "id", "type": "integer", "constraints": {"required": True}},
            {"name": "price", "type": "number"},
            {"name": "ok", "type": "boolean"},
            {"name": "day", "type": "date"},
        ]
    }
)


def test_quarantines_invalid_rows_with_reason() -> None:
    table = Table(
        columns=["day", "ok", "price", "id"],
        rows=[
            ["2025-01-31", "true", "1.5", "1"],
            ["", "", "", "2"],
            ["2025-02-30", "yes", "nan", ""],
        ],
    )
    valid, quarantine, report = validate(table, SCHEMA)

    assert valid.columns == ["id", "price", "ok", "day"]
    assert valid.rows == [["1", "1.5", "true", "2025-01-31"], ["2", "", "", ""]]
    assert len(quarantine) == 1
    assert quarantine[0][-1] == (
        "id: required; price: not a number; ok: not a boolean; day: not a date"
    )
    assert (report.rows_in, report.rows_valid, report.rows_invalid) == (3, 2, 1)
    assert report.null_counts == {"id": 0, "price": 1, "ok": 1, "day": 1}


def test_missing_schema_column_is_config_error() -> None:
    with pytest.raises(ConfigError):
        validate(Table(columns=["id"], rows=[]), SCHEMA)
