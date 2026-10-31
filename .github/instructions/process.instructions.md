---
applyTo: "src/datafactory/process/**"
---
# Process (processors)

- One transform = one file `process/processors/<name>.py` implementing `Processor`, registered in
  `process/registry.py`. Small, single-purpose, composable steps; configured from `dataset.yaml`.
- Pure functions of (input data, params) → output data. Deterministic: no network, no wall-clock, stable
  sort order. Same input → byte-identical output.
- Read from raw/staged zone, write to staged zone. Never mutate input files.
- Validate output against the dataset schema version; invalid rows go to a quarantine file with a reason,
  never silently dropped.
- PII: detect and drop/hash/aggregate as configured; default is drop.
- Record row counts in/out and quality metrics (null %, duplicates) for the datasheet.
