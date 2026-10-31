"""Read lists of JSON records from raw files; nested objects become ``a.b`` columns.

Numbers keep their exact source text; ``null`` becomes an empty string.
"""

import json
from collections.abc import Mapping
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.base import Reader


class JsonRecordsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str = "*.json"
    records_path: list[int | str] = []


class _Number(str):
    """A JSON number kept as its exact source text."""


def _compact(value: Any) -> str:
    if isinstance(value, _Number):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_compact(v) for v in value) + "]"
    if isinstance(value, dict):
        items = (f"{json.dumps(k, ensure_ascii=False)}:{_compact(v)}" for k, v in value.items())
        return "{" + ",".join(items) + "}"
    return json.dumps(value, ensure_ascii=False)


def _flatten(value: Any, prefix: str, out: dict[str, str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _flatten(item, f"{prefix}.{key}" if prefix else str(key), out)
    elif value is None:
        out[prefix] = ""
    elif isinstance(value, bool):
        out[prefix] = "true" if value else "false"
    elif isinstance(value, list):
        out[prefix] = _compact(value)
    else:
        out[prefix] = str(value)


def _records(path: Path, records_path: list[int | str]) -> list[Any]:
    data: Any = json.loads(path.read_text("utf-8"), parse_float=_Number, parse_int=_Number)
    try:
        for key in records_path:
            data = data[key]
    except (KeyError, IndexError, TypeError):
        raise ConfigError(f"{path.name}: records_path {records_path} not found") from None
    if data is None:
        return []
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ConfigError(f"{path.name}: records_path must point to a list of objects")
    return data


class JsonRecordsReader(Reader):
    name = "json_records"
    version = "1.0.0"

    def read(self, raw_dir: Path, files: list[str], params: Mapping[str, Any]) -> Table:
        p = JsonRecordsParams.model_validate(params)
        matched = [f for f in files if fnmatch(f, p.pattern)]
        if not matched:
            raise ConfigError(f"json_records: no raw file matches {p.pattern!r}")
        flat: list[dict[str, str]] = []
        for name in matched:
            for record in _records(raw_dir / name, p.records_path):
                row: dict[str, str] = {}
                _flatten(record, "", row)
                flat.append(row)
        columns = list(dict.fromkeys(key for row in flat for key in row))
        return Table(columns=columns, rows=[[row.get(c, "") for c in columns] for row in flat])
