"""Validate a table against a dataset's table schema. Invalid rows are quarantined with a reason."""

import re
from datetime import date

from datafactory.contracts.dataset import SchemaField, TableSchema
from datafactory.contracts.staged import QualityReport
from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError

_INTEGER = re.compile(r"^-?\d+$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BOOLEANS = {"true", "True", "TRUE", "1", "false", "False", "FALSE", "0"}


def validate(table: Table, schema: TableSchema) -> tuple[Table, list[list[str]], QualityReport]:
    """Return (valid rows in schema column order, quarantined rows + error, quality report)."""
    missing = [n for n in schema.field_names if n not in table.columns]
    if missing:
        raise ConfigError(f"columns missing for schema: {missing}")
    idx = [table.columns.index(n) for n in schema.field_names]
    valid: list[list[str]] = []
    quarantine: list[list[str]] = []
    for raw in table.rows:
        row = [raw[i] for i in idx]
        errors = [
            f"{f.name}: {err}"
            for f, v in zip(schema.fields, row, strict=True)
            if (err := _check(v, f))
        ]
        if errors:
            quarantine.append([*row, "; ".join(errors)])
        else:
            valid.append(row)
    nulls = {n: sum(1 for r in valid if r[i] == "") for i, n in enumerate(schema.field_names)}
    report = QualityReport(
        rows_in=len(table.rows),
        rows_valid=len(valid),
        rows_invalid=len(quarantine),
        null_counts=nulls,
    )
    return Table(columns=schema.field_names, rows=valid), quarantine, report


def _check(value: str, field: SchemaField) -> str | None:
    if value == "":
        return "required" if field.constraints.required else None
    ok = {
        "string": lambda v: True,
        "integer": lambda v: bool(_INTEGER.match(v)),
        "number": _is_number,
        "boolean": lambda v: v in _BOOLEANS,
        "date": _is_date,
    }[field.type](value)
    return None if ok else f"not a {field.type}"


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return value.lower() not in {"nan", "inf", "-inf", "infinity", "-infinity"}


def _is_date(value: str) -> bool:
    if not _DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
