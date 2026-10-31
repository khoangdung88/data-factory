---
applyTo: "tests/**,datasets/*/fixtures/**"
---
# Tests

- `pytest`. Unit tests mirror the source path: `src/datafactory/x/y.py` → `tests/x/test_y.py`
  (unique basenames, no `__init__.py` in test dirs).
- Tests are offline and deterministic: no network, no real clock/randomness without seeding/freezing.
  Mark tests that need real services `@pytest.mark.integration` (skipped in CI).
- Golden tests: `datasets/<slug>/fixtures/input/*` → run pipeline → compare with
  `fixtures/expected/*`. Changing an expected file is a behavior change: explain it in the PR.
- Fixtures are synthetic or anonymised, small (< 200 KB each), and license-safe.
- Never delete or weaken an existing test to make a change pass.
