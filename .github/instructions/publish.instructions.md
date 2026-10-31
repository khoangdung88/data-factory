---
applyTo: "src/datafactory/publish/**"
---
# Publish (publishers)

- One target = one file `publish/publishers/<name>.py` implementing `Publisher`, registered in
  `publish/registry.py`. Marketplace APIs live only in their publisher file.
- Package format: Frictionless Data Package (`datapackage.json`) + data files (CSV/Parquet) +
  `README.md` datasheet + `LICENSE`. Package path: `data/products/<slug>/<version>/`.
- A package always includes: schema version, dataset version (semver), license, source attribution,
  lineage (batch ids), row count, sha256 checksums, generated_at.
- Published versions are immutable. Re-publishing = new version.
- Never publish if quality gates in `dataset.yaml` fail or PII checks fail.
- Real publishing (network) only via explicit CLI flag; default is dry-run to the local products zone.
