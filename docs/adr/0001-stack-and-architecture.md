# 0001 — Stack and staged plugin architecture

- Status: proposed
- Date: 2026-10-31

## Context
Open-ended product, built mostly by AI agents in small PRs. Main risk: a new feature silently breaks an
older one. Rules must be enforceable by tools, not only by prose, and cheap to read (token budget).

## Decision
- Python 3.11+, `uv`, `ruff`, `mypy --strict`, `pytest`, Pydantic v2, Typer CLI.
- Three isolated stages (collect → process → publish) communicating only through `contracts` models and
  files in data zones (`raw`, `staged`, `products`). Isolation enforced by `import-linter`.
- Plugin-per-file with explicit registries; datasets are declarative YAML.
- Contracts versioned; released `schema/vN.json` immutable (CI guard). Products packaged as Frictionless
  Data Packages.
- Agent rules: one short `AGENTS.md` + path-scoped `.github/instructions/*.instructions.md`; no separate
  rules tree.
- No CHANGELOG / index files (merge-conflict magnets); history = Conventional Commit PR titles.

## Consequences
- Adding a source/transform/marketplace rarely touches existing code → low regression risk.
- Some duplication between plugins is accepted in exchange for isolation.
- Processing library (pandas/polars/duckdb) and storage beyond local disk are deferred to later ADRs.
