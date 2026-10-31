from pathlib import Path

from conftest import NOW
from datafactory.core.config import Settings
from datafactory.pipeline.runner import run


def test_local_folder_copies_package(settings: Settings) -> None:
    result = run("sample-csv", settings=settings, now=NOW)

    assert result.destinations == [str(settings.data_dir / "exports" / "sample-csv-1.0.0")]
    dest = Path(result.destinations[0])
    assert sorted(p.name for p in dest.iterdir()) == [
        "LICENSE",
        "README.md",
        "data.csv",
        "datapackage.json",
    ]
