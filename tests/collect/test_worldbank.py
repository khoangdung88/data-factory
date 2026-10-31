import json
from pathlib import Path

import pytest

from datafactory.collect.base import FetchContext
from datafactory.collect.connectors import worldbank
from datafactory.collect.connectors.worldbank import WorldBankConnector
from datafactory.core.errors import CollectError

COUNTRIES = [
    {"page": 1, "pages": 1},
    [
        {"id": "VNM", "region": {"id": "EAS"}},
        {"id": "WLD", "region": {"id": "NA"}},
        {"id": "AUS", "region": {"id": "EAS"}},
    ],
]


def _page(page: int, pages: int) -> bytes:
    return json.dumps([{"page": page, "pages": pages}, [{"value": page}]]).encode()


def test_fetches_economies_and_all_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, retries: int = 3) -> bytes:
        calls.append(url)
        if "/country?" in url:
            return json.dumps(COUNTRIES).encode()
        return _page(int(url.rsplit("page=", 1)[1]), 2)

    monkeypatch.setattr(worldbank, "http_get", fake_get)
    params = {"indicators": ["SP.POP.TOTL"], "date": "2020:2021"}
    source = WorldBankConnector().fetch(params, FetchContext(dest=tmp_path, dataset_dir=tmp_path))

    assert "/country/AUS;VNM/indicator/SP.POP.TOTL?" in calls[1]
    assert len(calls) == 3
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "countries.json",
        "indicator-SP.POP.TOTL-p001.json",
        "indicator-SP.POP.TOTL-p002.json",
    ]
    assert (tmp_path / "indicator-SP.POP.TOTL-p002.json").read_bytes() == _page(2, 2)
    assert source.endswith("/country/economies/indicator/SP.POP.TOTL?date=2020:2021")


def test_api_error_message_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    error = [{"message": [{"id": "120", "value": "The provided parameter value is not valid"}]}]
    monkeypatch.setattr(worldbank, "http_get", lambda url, retries=3: json.dumps(error).encode())
    params = {"indicators": ["NOPE"], "countries": "VNM", "date": "2020"}
    with pytest.raises(CollectError, match="API error"):
        WorldBankConnector().fetch(params, FetchContext(dest=tmp_path, dataset_dir=tmp_path))


@pytest.mark.integration
def test_live_api(tmp_path: Path) -> None:
    params = {"indicators": ["SP.POP.TOTL"], "countries": "VNM", "date": "2020:2021"}
    WorldBankConnector().fetch(params, FetchContext(dest=tmp_path, dataset_dir=tmp_path))
    data = json.loads((tmp_path / "indicator-SP.POP.TOTL-p001.json").read_text())
    assert {r["date"] for r in data[1]} == {"2020", "2021"}
