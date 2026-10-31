"""Deterministic CSV read/write (UTF-8, ``\\n`` line endings)."""

import csv
import io
from pathlib import Path

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.core.storage import write_text


def read_csv(path: Path) -> Table:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ConfigError(f"{path.name} is empty")
    header, body = rows[0], rows[1:]
    bad = [i for i, r in enumerate(body, start=2) if len(r) != len(header)]
    if bad:
        raise ConfigError(f"{path.name}: wrong column count on lines {bad[:5]}")
    return Table(columns=header, rows=body)


def write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    write_text(path, buf.getvalue())
