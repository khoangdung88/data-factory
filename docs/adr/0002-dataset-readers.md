# 0002 — Raw-to-table readers selected per dataset

- Status: accepted
- Date: 2026-10-31

## Context
The process stage only understood a single CSV file. Real sources deliver other raw formats (the World
Bank API returns paginated nested JSON), and connectors must store raw data as-is.

## Decision
- `DatasetSpec` gets an optional `reader: {plugin, params}` (default `csv`).
- Readers implement `process.base.Reader.read(raw_dir, files, params) -> Table`, live one per file in
  `process/readers/`, are registered explicitly in `READERS`, and are independent (import-linter).
- `csv` keeps the previous behavior (exactly one CSV); `json_records` flattens nested JSON records.

## Consequences
- Existing datasets need no change; their golden outputs are byte-identical.
- A new raw format = a new reader file + one registry line; processors stay format-agnostic.
- Reader name/version is not yet recorded in package lineage.
