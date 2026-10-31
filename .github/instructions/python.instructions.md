---
applyTo: "src/**/*.py"
---
# Python code

- Python 3.11+, full type hints, `mypy --strict` clean, `ruff` clean (line length 100).
- Data crossing a module boundary is a Pydantic model from `contracts/` — never a raw `dict`.
- Config only via `core.config.Settings` (env prefix `DF_`); no `os.environ` elsewhere.
- Paths only via `core` storage helpers; no hard-coded `data/...` strings.
- Raise typed errors from `core.errors` (`DataFactoryError` subclasses); never bare `Exception`, never
  swallow errors silently.
- Registries are explicit dicts in each stage's `registry.py`; no auto-discovery or import side effects.
- Shared stage code must not branch on plugin names (`if name == "x"`). Missing behavior → extend the
  interface instead.
- New dependency → justify in the PR; heavy or architectural ones need an ADR.
- No commented-out code, no `print` (use `core.logging`), no TODO without an issue link.
