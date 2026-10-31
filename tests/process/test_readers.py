import json
from pathlib import Path

import pytest

from datafactory.contracts.table import Table
from datafactory.core.errors import ConfigError
from datafactory.process.readers.csv_file import CsvFileReader
from datafactory.process.readers.json_records import JsonRecordsReader


def test_json_records_flattens_and_keeps_number_text(tmp_path: Path) -> None:
    page = [{"page": 1}, [{"a": {"id": "X"}, "v": 1.50, "n": None, "b": True, "l": [1, "x", None]}]]
    (tmp_path / "p1.json").write_text(json.dumps(page).replace("1.5", "1.50"))
    (tmp_path / "p2.json").write_text(json.dumps([{}, [{"a": {"id": "Y"}, "extra": 7}]]))
    (tmp_path / "empty.json").write_text(json.dumps([{}, None]))
    (tmp_path / "other.txt").write_text("ignored")

    table = JsonRecordsReader().read(
        tmp_path, ["empty.json", "other.txt", "p1.json", "p2.json"], {"records_path": [1]}
    )

    assert table == Table(
        columns=["a.id", "v", "n", "b", "l", "extra"],
        rows=[["X", "1.50", "", "true", '[1,"x",null]', ""], ["Y", "", "", "", "", "7"]],
    )


def test_json_records_errors(tmp_path: Path) -> None:
    (tmp_path / "x.json").write_text(json.dumps({"rows": "nope"}))
    reader = JsonRecordsReader()
    with pytest.raises(ConfigError, match="no raw file"):
        reader.read(tmp_path, ["x.json"], {"pattern": "*.csv"})
    with pytest.raises(ConfigError, match="not found"):
        reader.read(tmp_path, ["x.json"], {"records_path": ["missing"]})
    with pytest.raises(ConfigError, match="list of objects"):
        reader.read(tmp_path, ["x.json"], {"records_path": ["rows"]})


def test_csv_reader_needs_exactly_one_csv(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x\n1\n")
    assert CsvFileReader().read(tmp_path, ["a.csv"], {}).rows == [["1"]]
    with pytest.raises(ConfigError):
        CsvFileReader().read(tmp_path, ["a.csv", "b.csv"], {})
