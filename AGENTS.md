# AGENTS.md

Single source of truth for every AI agent (Devin, Copilot, Cursor, Claude, Codex) and human in this repo.
Read this file fully. Read a `.github/instructions/*.instructions.md` file **only** when you touch the
paths in its `applyTo` header. Do not load other docs unless the task needs them.

## Product

`data-factory` turns raw data into **sellable data products**:
**collect** (connectors → raw zone) → **process** (clean, validate, enrich → staged zone) →
**publish** (package + datasheet + license → products zone / marketplace).
Unit of work = a **dataset** declared in `datasets/<slug>/dataset.yaml`.

## Golden rules

1. **Add, don't modify.** New capability = new plugin file or new dataset folder. Editing existing
   plugins, contracts or released schemas needs a reason in the PR and must keep their tests green.
2. **Stages are isolated.** `collect`, `process`, `publish` never import each other. They exchange data
   only through `contracts` models and files in the data zones. Enforced by `import-linter`.
3. **Contracts are versioned and immutable.** A merged `datasets/*/schema/vN.json` is never edited.
   Breaking change → add `vN+1.json`, bump dataset `version`, label PR `breaking`. Enforced by CI.
4. **Every behavior has a test; every dataset has a golden test** (fixture input → expected output).
   Never change an expected-output fixture just to make a test pass — explain why in the PR.
5. **One feature = one spec = one PR.** Spec in `docs/features/<slug>.md` (status `approved` before
   code). `feat` PRs without a spec/ADR change fail CI. Aim for < 400 changed lines.
6. **Legal & clean data only.** Every source declares license/terms allowing our use; respect robots.txt
   and rate limits; no PII in published products. No secrets or real data in git.
7. **Decisions go in ADRs** (`docs/adr/`) when they change architecture, dependencies or contracts.
8. **Don't invent scope.** Ambiguous product decision (pricing, license, fields) → stop and ask.

## Layout

| Path | Purpose |
|---|---|
| `src/datafactory/core/` | config, logging, errors, storage paths. Imports nothing from the project |
| `src/datafactory/contracts/` | Pydantic models crossing stage boundaries (batch manifest, dataset spec, package) |
| `src/datafactory/collect/` | `Connector` interface + `connectors/<name>.py` plugins + registry |
| `src/datafactory/process/` | `Processor` interface + `processors/<name>.py` plugins + registry |
| `src/datafactory/publish/` | `Publisher` interface + `publishers/<name>.py` plugins + registry |
| `src/datafactory/pipeline/` | orchestration: reads `dataset.yaml`, runs stages, records lineage |
| `src/datafactory/cli.py` | Typer CLI (thin, no logic) |
| `datasets/<slug>/` | `dataset.yaml`, `schema/vN.json`, `README.md` (datasheet), `fixtures/` |
| `docs/` | `architecture.md`, `features/` specs, `adr/` decisions |
| `data/` | local data zones `raw/ staged/ products/` — git-ignored |

Import direction (enforced): `cli → pipeline → collect | process | publish → contracts → core`.

## Workflow (every task)

1. Find or write the spec (`docs/features/_template.md`). Small fixes/chores: an issue is enough.
2. `grep` for existing code before writing new code. Reuse; don't duplicate.
3. Write the failing test / golden fixture first, then the code.
4. `make check` green (ruff, mypy, import-linter, pytest).
5. Update docs the change makes stale (spec status → `done`, datasheet, architecture if needed).
6. PR: Conventional Commit title `type(scope): summary`, body = `.github/PULL_REQUEST_TEMPLATE.md`.

Scopes: `core contracts collect process publish pipeline cli datasets docs ci agent`.
Branches: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>` (agents may prefix `devin/`).
Avoid shared append-only files (no CHANGELOG, no index lists) — they cause merge conflicts.

## Commands

```bash
make install   # uv sync + pre-commit install
make check     # what CI runs; must pass before PR
make fmt       # auto-format + autofix
```

## Definition of Done

- [ ] Scope matches spec/issue; nothing unrelated changed
- [ ] `make check` green locally and in CI; old tests untouched or justified
- [ ] New plugin/dataset has unit + golden tests and offline fixtures (no network in tests)
- [ ] Docs/datasheet updated; ADR added if a contract or dependency changed
- [ ] No secrets, PII or real data committed
