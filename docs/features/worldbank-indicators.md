---
status: done
issue: ""
---
# First real product: World Bank macro indicators

## Problem
The factory had no real source. The owner has no data yet and asked Devin to pick one and deliver a
first packaged dataset without further confirmation.

## Decision
Source = World Bank Indicators API v2: free, no key, CC BY 4.0 (commercial reuse allowed with
attribution), stable JSON. Product = long-format panel `wb-macro-indicators` (5 core WDI indicators,
all ~217 economies, 2000-2025, aggregates excluded).

## Scope
- Connector `worldbank`: paginated indicator pages + country list (to exclude aggregates), raw as-is.
- `DatasetSpec.reader` (default `csv` = previous behavior) + reader registry: `csv`, `json_records`
  (flatten nested JSON, keep number text exactly).
- Processors: `drop_rows_missing`, `rename_columns`, `sort_rows`.
- Dataset `datasets/wb-macro-indicators/` with schema v1, datasheet, synthetic golden fixtures.

## Out of scope
Marketplace publishers, scheduled refresh, pricing, wide/pivoted layouts, more indicators.

## Acceptance criteria
- [x] `datafactory run wb-macro-indicators` builds `data/products/wb-macro-indicators/1.0.0/` from the live API
- [x] Offline golden test + connector tests with fake HTTP; live test marked `integration`
- [x] `sample-csv` golden output unchanged

## Impact on existing features
Additive. `process/stage.py` now delegates file reading to the dataset's reader; the default `csv`
reader keeps the old "exactly one CSV" behavior, so existing datasets need no change.
