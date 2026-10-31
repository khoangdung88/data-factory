# 0003 — Server-rendered web UI with FastAPI

- Status: accepted
- Date: 2026-10-31

## Context
The owner wants a UI to run the pipeline and inspect batches/products. It must stay small, testable
offline, and must not change the stage architecture.

## Decision
- Add package `datafactory.ui`: FastAPI app + Jinja2 templates (server-rendered HTML, no JS build), served
  by uvicorn via `datafactory ui`. New runtime dependencies: `fastapi`, `uvicorn`, `jinja2`,
  `python-multipart`; dev: `httpx` (FastAPI `TestClient`).
- Layering: `cli → ui → pipeline → stages → contracts → core`. The UI calls `pipeline.run` and only reads
  zone files through `contracts` models; it never writes to data zones itself.
- Runs execute in-process in a background thread, at most one per dataset; run state and logs are kept in
  memory (lost on restart).
- Binds to `127.0.0.1` by default; no authentication.

## Consequences
- Alternatives rejected: Streamlit (re-runs the whole script per interaction, hard to unit-test), SPA
  (separate JS toolchain and API layer).
- Not safe to expose publicly as-is; multi-user/hosted use needs auth and a job queue (new ADR).
- Long runs block one worker thread each; acceptable for a local single-user tool.
