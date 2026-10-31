# User guide

How to install data-factory, build a data product, read the output and fix common errors.
For internals see [`technical-guide.md`](technical-guide.md).

## 1. Install

Requirements: Linux/macOS/WSL, Git, [uv](https://docs.astral.sh/uv/) (it installs Python 3.11 for you).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # once, if uv is missing
git clone https://github.com/khoangdung88/data-factory.git && cd data-factory
make install                                       # dependencies + git hooks
uv run datafactory version                         # check it works
```

## 2. Build a product in one command

```bash
uv run datafactory run wb-macro-indicators
```

```text
batch: c6b9e89f34fa
package: data/products/wb-macro-indicators/1.0.0
published: data/exports/wb-macro-indicators-1.0.0
```

This calls the World Bank API (internet needed, ~10 s), cleans and validates the data and writes a
ready-to-sell package. `sample-csv` is an offline demo dataset: `uv run datafactory run sample-csv`.

## 3. CLI reference

`datafactory run <slug> [OPTIONS]`, where `<slug>` is a folder name in `datasets/`.

| Option | Meaning |
|---|---|
| *(none)* | Run collect → process → publish |
| `--stage collect` | Only fetch from the source into `data/raw/` |
| `--stage process` | Only clean/validate a raw batch into `data/staged/` |
| `--stage publish` | Only package a processed batch into `data/products/` and run publishers |
| `--batch <id>` | Batch to process/publish (default: latest raw batch) |
| `--release` | Also run remote (marketplace) publishers; without it nothing leaves your machine |

Exit code `0` = success, `1` = expected error (message printed as `error: ...`).

Settings (environment variables or a `.env` file in the repo root):

| Variable | Default | Meaning |
|---|---|---|
| `DF_DATA_DIR` | `data` | Root of the data zones |
| `DF_DATASETS_DIR` | `datasets` | Where dataset definitions live |

## 4. What you get

```text
data/
├── raw/<slug>/<batch_id>/        source files exactly as downloaded + _manifest.json
├── staged/<slug>/<batch_id>/     data.csv (valid rows), quarantine.csv (rejected rows + _error), _manifest.json
├── products/<slug>/<version>/    the product (never changes once written)
└── exports/<slug>-<version>/     copy made by the local_folder publisher
```

A product folder is what you upload or sell:

| File | Content |
|---|---|
| `data.csv` | Clean table, UTF-8, header row, columns as in the schema |
| `datapackage.json` | [Frictionless Data Package](https://specs.frictionlessdata.io/data-package/): title, version, license, sources, schema, sha256, row counts, lineage, quality |
| `README.md` | Datasheet for buyers (copied from `datasets/<slug>/README.md`) |
| `LICENSE` | License name and URL |

Check quality before selling: `quality` in `datapackage.json` (`rows_in`, `rows_valid`, `rows_invalid`,
`null_counts`) and the rows in `staged/<slug>/<batch_id>/quarantine.csv`.

## 5. Run behaviour you can rely on

- **Re-running is safe.** Same source data → same `batch_id`, nothing duplicated. Same data and version
  → the existing product is reused.
- **Products are immutable.** If the source data changed but `version` did not, publish stops with
  `exists with different data; bump version`. Bump `version` in `dataset.yaml` (e.g. `1.0.0` → `1.1.0`) and run again.
- **Quality gates block bad products.** Too few valid rows or too many rejected rows → error
  `valid rows < min_rows` or `invalid ratio ... > max`; nothing is published.
- `data/` is git-ignored: products stay on your machine until a publisher sends them somewhere.

## 6. Create your own dataset

1. Create `datasets/<slug>/` (`<slug>` = lowercase words joined by `-`).
2. `dataset.yaml`:

```yaml
slug: my-dataset
title: Human readable title
description: One paragraph for buyers.
version: 1.0.0                     # bump on every data or schema change you publish
schema_version: 1                  # -> schema/v1.json
license: {name: CC-BY-4.0, path: https://creativecommons.org/licenses/by/4.0/}
source:
  plugin: local_file               # connector, see table below
  license: Terms that allow us to use and resell this source
  params: {path: input/my.csv}     # relative to the dataset folder
reader: {plugin: csv}              # optional, default csv
processing:                        # optional, applied in order
  - plugin: select_columns
    params: {columns: [id, name, price]}
quality: {min_rows: 1, max_invalid_ratio: 0.0}
publish:
  - plugin: local_folder
pricing: {model: undecided}        # free-form, informational
```

3. `schema/v1.json` — the columns of the final table:

```json
{"fields": [
  {"name": "id", "type": "integer", "description": "Row id", "constraints": {"required": true}},
  {"name": "name", "type": "string", "description": "Name"},
  {"name": "price", "type": "number", "description": "Price in USD"}
]}
```

Types: `string`, `integer`, `number`, `boolean` (`true/false/1/0`), `date` (`YYYY-MM-DD`). Empty value =
null; a `required` null or a wrong type sends the row to quarantine.

4. `README.md` — datasheet: field table, coverage, update frequency, source & license, limitations.
   Publishing fails without it.
5. `uv run datafactory run <slug>`. To merge it into the repo, add golden fixtures (see the technical
   guide) and open a PR.

### Available plugins

| Stage | Plugin | Params |
|---|---|---|
| connector | `local_file` | `path` |
| connector | `worldbank` | `indicators` (list), `date` (`2000:2025`), `countries` (`economies` \| `all` \| `VNM;USA`), `per_page` |
| reader | `csv` | — (exactly one `.csv` in the batch) |
| reader | `json_records` | `pattern` (glob, default `*.json`), `records_path` (list of keys/indexes to the record list) |
| processor | `select_columns` | `columns` |
| processor | `rename_columns` | `mapping` (`old: new`) |
| processor | `drop_rows_missing` | `columns` (drop rows where any is empty) |
| processor | `sort_rows` | `by` |
| publisher | `local_folder` | `target_dir` (default `exports`, relative to `DF_DATA_DIR`) |

## 7. Troubleshooting

| Message | Cause → fix |
|---|---|
| `dataset 'x' not found` | No `datasets/x/dataset.yaml`; check the slug / `DF_DATASETS_DIR` |
| `invalid dataset 'x': ...` | `dataset.yaml` field missing, misspelt or wrong type; read the detail |
| `unknown connector/processor/reader 'x'` | Plugin name typo; see the table above |
| `no raw batch for 'x'; run the collect stage first` | Run without `--stage` or with `--stage collect` |
| `batch ... is not processed yet` | Run `--stage process` for that batch first |
| `valid rows < min_rows` / `invalid ratio ... > max` | Inspect `quarantine.csv`; fix the source/processing or adjust `quality` deliberately |
| `exists with different data; bump version` | Data changed for an existing version; bump `version` |
| `datasheet README.md is required` | Add `datasets/<slug>/README.md` |
| `worldbank: GET ... failed` | Network/API problem; retried 3 times; run again later |
