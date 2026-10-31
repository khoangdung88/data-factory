# Technical guide

Reference for developers and AI agents extending data-factory. Overview and diagram:
[`architecture.md`](architecture.md); rules: [`../AGENTS.md`](../AGENTS.md); usage:
[`user-guide.md`](user-guide.md).

## 1. Components

| Module | Responsibility | Key names |
|---|---|---|
| `core/config.py` | Settings from env/`.env` (prefix `DF_`) | `Settings`, `get_settings()` |
| `core/errors.py` | Typed errors; CLI turns them into exit code 1 | `DataFactoryError` and subclasses |
| `core/storage.py` | Zone paths, sha256, atomic text writes | `Zone`, `batch_dir`, `product_dir`, `MANIFEST_FILE` |
| `contracts/` | Pydantic models crossing stage boundaries | `DatasetSpec`, `TableSchema`, `Table`, `BatchManifest`, `StagedManifest`, `QualityReport`, `DataPackage` |
| `collect/` | Source → raw zone | `Connector`, `CONNECTORS`, `run_collect` |
| `process/` | Raw → staged zone | `Reader`, `Processor`, `READERS`, `PROCESSORS`, `validate`, `run_process` |
| `publish/` | Staged → product + targets | `Publisher`, `PUBLISHERS`, `build_package`, `run_publish` |
| `pipeline/runner.py` | Load dataset, pick batch, run stages | `run`, `Stage`, `load_dataset`, `latest_batch` |
| `cli.py` | Typer adapter, no logic | `datafactory run`, `datafactory version` |

Import direction `cli → pipeline → collect | process | publish → contracts → core` and plugin
independence are enforced by `import-linter` (`pyproject.toml`).

## 2. Data flow and contracts

1. **Collect** — `run_collect(spec, dataset_dir, settings, now)`
   - Connector writes files into a temp dir and returns a source description (URL/path).
   - `batch_id` = first 12 hex of sha256(connector name+version, params, file checksums): unchanged data
     reuses the existing batch (idempotent).
   - Writes `raw/<slug>/<batch_id>/_manifest.json` (`BatchManifest`: connector, source, license,
     `fetched_at`, files with sha256/bytes), then renames the temp dir into place (atomic).
2. **Process** — `run_process(spec, schema, batch_id, settings)`
   - Reader (`dataset.yaml` `reader`, default `csv`) turns raw files into a `Table` (all values strings).
   - Processors run in order; each returns a new `Table` (pure, deterministic).
   - `validate` checks columns/types/required against `schema/vN.json`; bad rows → `quarantine.csv`
     with `_error`; `QualityReport` counts rows and nulls.
   - Writes `staged/<slug>/<batch_id>/{data.csv, quarantine.csv, _manifest.json}` (`StagedManifest`).
3. **Publish** — `run_publish(spec, schema, batch_id, *, dataset_dir, settings, now, release)`
   - `build_package` enforces `quality.min_rows` and `quality.max_invalid_ratio`, requires the datasheet,
     builds `DataPackage` (Frictionless) with lineage (batch ids, connector + processor versions), hashes
     and quality, writes `products/<slug>/<version>/` atomically.
   - Existing version with same data hash → reused; different hash → `ProductExistsError`.
   - Publishers from `dataset.yaml` run in order; `remote = True` publishers are skipped unless `release`.

CSV I/O is UTF-8 with `\n` line endings, so identical input gives byte-identical output.

## 3. Versioning

| Thing | Rule |
|---|---|
| `dataset.yaml` `version` | Semver; one immutable product per version |
| `schema/vN.json` | Never edited after merge (CI); breaking change → `vN+1.json` + bump `schema_version` and `version` |
| Plugin `version` class attribute | Bump when output changes; recorded in lineage |
| Contracts (`contracts/`) | Additive optional fields only; anything else → ADR |

## 4. Extending

Every extension = new file + one registry line + tests. Do not edit other plugins.

| Add | File | Interface | Register in |
|---|---|---|---|
| Source | `collect/connectors/<name>.py` | `Connector.fetch(params, ctx) -> str` (write to `ctx.dest`) | `collect/registry.py` `CONNECTORS` |
| Raw format | `process/readers/<name>.py` | `Reader.read(raw_dir, files, params) -> Table` | `process/registry.py` `READERS` |
| Transform | `process/processors/<name>.py` | `Processor.apply(table, params) -> Table` | `process/registry.py` `PROCESSORS` |
| Target / marketplace | `publish/publishers/<name>.py` | `Publisher.publish(ctx, params) -> str`; set `remote = True` if it leaves the machine | `publish/registry.py` `PUBLISHERS` |

Plugin conventions: class attributes `name`, `version`; validate `params` with a Pydantic model
(`extra="forbid"`); raise `ConfigError` for bad params, `CollectError` for source failures. Connectors keep
raw bytes as-is, identify themselves (User-Agent), rate-limit and never log secrets; secrets come from
`Settings` / env, never from `dataset.yaml`. Processors must not do I/O.

Skeleton (processor):

```python
class MyParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column: str

class MyStep(Processor):
    name = "my_step"
    version = "1.0.0"

    def apply(self, table: Table, params: Mapping[str, Any]) -> Table:
        p = MyParams.model_validate(params)
        ...
        return Table(columns=..., rows=...)
```

## 5. Testing

| Test | Where | Notes |
|---|---|---|
| Unit tests per plugin | `tests/<stage>/` | Offline; fake HTTP by monkeypatching the connector's `http_get` |
| Golden test | `tests/test_golden_datasets.py` | Auto-runs every `datasets/*/`: copies `fixtures/input/` (raw batch incl. `_manifest.json`) into a temp raw zone, runs process + publish with a fixed clock, compares with `fixtures/expected/` byte for byte |
| Live tests | `@pytest.mark.integration` | Skipped by `make check`/CI; run with `uv run pytest -m integration` |

Golden fixtures must be synthetic or license-cleared and small. Create them by running the real pipeline
with fake source responses into a temp `DF_DATA_DIR`, then copying the raw batch to `fixtures/input/`
and the product to `fixtures/expected/`. Changing an expected file is a behaviour change: explain it in the
PR. Pre-commit whitespace fixers skip `datasets/*/fixtures/` so recorded bytes keep matching their hashes.

## 6. Quality gates in CI

`.github/workflows/ci.yml` runs `make check` (ruff, ruff format, mypy strict, import-linter, pytest) and
repo rules: Conventional Commit PR title, `feat` PRs must change `docs/features/` or `docs/adr/`, released
`schema/vN.json` files cannot be modified, deleted or renamed.

## 7. Decisions

- [ADR 0001](adr/0001-stack-and-architecture.md) — stack and stage/plugin architecture.
- [ADR 0002](adr/0002-dataset-readers.md) — raw-to-table readers per dataset.
- Feature specs: [`features/`](features/).
