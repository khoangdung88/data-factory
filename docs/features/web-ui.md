---
status: done  # draft | approved | done
issue: "owner request: UI to run data-factory"
---
# Web UI

## Problem
Running and inspecting pipelines needs the CLI plus reading JSON/CSV files by hand. The owner wants a
browser UI to run datasets and check results.

## Scope
- `datafactory ui [--host 127.0.0.1] [--port 8000]` starts a local web app (`src/datafactory/ui/`).
- Datasets page: every `datasets/<slug>/` with title, version, connector, latest batch/product, or the
  load error.
- Dataset page: run form (all stages or one, batch, release), raw batches with quality, products, recent
  runs.
- Runs execute in a background thread (one at a time per dataset); run page shows status, logs, result or
  error and refreshes until done.
- Batch page: raw files, staged quality, preview of `data.csv` and `quarantine.csv`.
- Product page: metadata (license, sources, lineage, quality, schema), data preview, zip download.

## Out of scope
Authentication, multi-user deployment, editing `dataset.yaml` in the browser, persisting run history
across restarts, scheduling.

## Acceptance criteria
- [x] Datasets page lists `sample-csv` and shows invalid datasets with their error instead of failing.
- [x] Posting the run form runs the pipeline and the run page reports success with batch and package.
- [x] A failing run reports the `DataFactoryError` message; a second run of a busy dataset is refused.
- [x] Batch and product pages show quality numbers and previews; download returns a zip of the product.
- [x] Unknown dataset/batch/version or path-traversal names return 404.
- [x] `ui` only uses `pipeline`, `contracts`, `core` (import-linter layer `cli → ui → pipeline`).

## Impact on existing features
None: new `ui` package, new `ui` CLI command, new dependencies (ADR 0003). Pipeline and stages unchanged.
