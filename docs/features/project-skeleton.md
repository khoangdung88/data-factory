---
status: done
issue: ""
---
# Project skeleton: contracts, plugin interfaces, pipeline, sample dataset

## Problem
Rules reference interfaces and a pipeline that do not exist yet. Agents need a working end-to-end path to
copy from.

## Scope
- `core`: `Settings` (env prefix `DF_`), errors, logging, storage path helpers for data zones.
- `contracts`: `BatchManifest`, `DatasetSpec` (parsed `dataset.yaml`), `PackageManifest`.
- `collect`/`process`/`publish`: `base.py` interface + `registry.py` + one plugin each:
  `local_file` connector, `select_columns` processor, `local_folder` publisher (Frictionless package).
- `pipeline.run(slug)` + CLI `datafactory run <slug> [--stage collect|process|publish]`.
- `datasets/sample-csv/` with schema `v1.json`, datasheet, golden fixtures; generic golden test that runs
  every dataset in `datasets/` offline.

## Out of scope
Real sources, marketplaces, scheduling, cloud storage, processing library choice.

## Acceptance criteria
- [x] `datafactory run sample-csv` produces `data/products/sample-csv/1.0.0/datapackage.json`
- [x] Each stage can run alone from the previous zone
- [x] Golden test passes for every dataset folder; `make check` green

## Impact on existing features
None (first feature).
