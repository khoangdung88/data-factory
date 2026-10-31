"""World Bank Indicators API v2 (https://api.worldbank.org/v2), data licensed CC BY 4.0.

Writes the API responses as-is: ``countries.json`` (when ``countries: economies``) and one
``indicator-<code>-p<NNN>.json`` per page.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from datafactory.collect.base import Connector, FetchContext
from datafactory.core.errors import CollectError

BASE_URL = "https://api.worldbank.org/v2"
ECONOMIES = "economies"
AGGREGATE_REGION = "NA"
REQUEST_INTERVAL_S = 1.0


class WorldBankParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicators: list[str] = Field(min_length=1)
    countries: str = Field(
        default=ECONOMIES,
        description="'economies' (all countries, no regional aggregates), 'all', or 'VNM;USA'",
    )
    date: str = Field(pattern=r"^\d{4}(:\d{4})?$")
    per_page: int = Field(default=20000, ge=1, le=32500)


def http_get(url: str, retries: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "data-factory"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                body: bytes = resp.read()
                return body
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries:
                raise CollectError(f"worldbank: GET {url} failed: {exc}") from exc
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _get_json(url: str) -> tuple[bytes, list[Any]]:
    body = http_get(url)
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise CollectError(f"worldbank: non-JSON response from {url}") from exc
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise CollectError(f"worldbank: unexpected response from {url}")
    if "message" in data[0]:
        raise CollectError(f"worldbank: API error {data[0]['message']} for {url}")
    return body, data


class WorldBankConnector(Connector):
    name = "worldbank"
    version = "1.0.0"

    def fetch(self, params: Mapping[str, Any], ctx: FetchContext) -> str:
        p = WorldBankParams.model_validate(params)
        requests = 0

        def get(url: str) -> tuple[bytes, list[Any]]:
            nonlocal requests
            if requests:
                time.sleep(REQUEST_INTERVAL_S)
            requests += 1
            return _get_json(url)

        countries = p.countries
        if countries == ECONOMIES:
            body, data = get(f"{BASE_URL}/country?format=json&per_page=1000")
            (ctx.dest / "countries.json").write_bytes(body)
            rows = data[1] if len(data) > 1 and data[1] else []
            countries = ";".join(
                sorted(c["id"] for c in rows if c["region"]["id"] != AGGREGATE_REGION)
            )
        for indicator in p.indicators:
            page, pages = 1, 1
            while page <= pages:
                query = urllib.parse.urlencode(
                    {"format": "json", "date": p.date, "per_page": p.per_page, "page": page}
                )
                url = f"{BASE_URL}/country/{countries}/indicator/{indicator}?{query}"
                body, data = get(url)
                (ctx.dest / f"indicator-{indicator}-p{page:03d}.json").write_bytes(body)
                pages = int(data[0].get("pages") or 1)
                page += 1
        indicators = ";".join(p.indicators)
        return f"{BASE_URL}/country/{countries}/indicator/{indicators}?format=json&date={p.date}"
