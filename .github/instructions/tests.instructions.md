---
applyTo: "tests/**,datasets/*/fixtures/**"
---
# Tests

- `pytest`. Unit tests mirror the source path: `src/datafactory/x/y.py` → `tests/x/test_y.py`
  (unique basenames, no `__init__.py` in test dirs).
- Tests are offline and deterministic: no network, no real clock/randomness without seeding/freezing.
  Mark tests that need real services `@pytest.mark.integration` (skipped in CI).
- Golden tests (`tests/test_golden_datasets.py`, automatic for every dataset): `fixtures/input/` is a
  recorded raw batch (data files + `_manifest.json`), `fixtures/expected/` is the product folder it must
  produce byte for byte. Changing an expected file is a behavior change: explain it in the PR.
- Fixtures are synthetic or anonymised, small (< 200 KB each), and license-safe.
- Never delete or weaken an existing test to make a change pass.
