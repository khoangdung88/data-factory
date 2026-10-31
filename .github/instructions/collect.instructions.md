---
applyTo: "src/datafactory/collect/**"
---
# Collect (connectors)

- One source = one file `collect/connectors/<name>.py` implementing `Connector`, registered in
  `collect/registry.py`. Do not edit other connectors.
- A connector only fetches and writes to the **raw zone** as-is plus a `BatchManifest` (source, URL/query,
  fetched_at, row/file count, sha256, license, connector version). No cleaning here.
- Idempotent and resumable: same params → same batch path; re-running must not duplicate data.
- Be a good citizen: honor robots.txt and the source's ToS, set a descriptive User-Agent, rate-limit,
  retry with backoff on 429/5xx, use official APIs when they exist.
- The source's license/terms must allow our intended use (incl. resale). Record it in the manifest. If
  unknown → do not implement; ask.
- Credentials come from `Settings`; never log them. Tests use recorded fixtures, never live calls.
