---
applyTo: "datasets/**"
---
# Datasets (data products)

- Folder `datasets/<slug>/` (kebab-case): `dataset.yaml`, `schema/vN.json`, `README.md`, `fixtures/`.
- `dataset.yaml` is declarative: source connector + params, ordered processor steps, schema version,
  quality gates, publish targets, license, pricing metadata. Prefer config over new code.
- `schema/vN.json` (Frictionless Table Schema) is immutable once merged. Breaking change (remove/rename/
  retype a field, change meaning) → new `vN+1.json` + major `version` bump. Adding an optional field →
  minor bump, still a new schema file.
- `README.md` is the buyer-facing datasheet: description, fields, coverage, update frequency, source &
  license, known limitations, sample rows.
- Every dataset has golden fixtures (`fixtures/input`, `fixtures/expected`) so CI proves it still works.
