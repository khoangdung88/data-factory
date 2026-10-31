---
applyTo: "docs/**"
---
# Docs

- Feature spec: `docs/features/<slug>.md` from `_template.md`. Status: `draft → approved → done`.
  Code starts only when `approved`. Keep it short: problem, scope, out of scope, acceptance criteria.
- ADR: `docs/adr/NNNN-<slug>.md` from `_template.md`, next free number. Never edit an accepted ADR's
  decision; supersede it with a new ADR.
- `docs/architecture.md` describes the current system only; update it in the PR that changes it.
- English, concise, no duplication of `AGENTS.md`. Exception: `docs/user-guide.vi.md` is the Vietnamese
  translation of `docs/user-guide.md`; change both in the same PR.
