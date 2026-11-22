# Known Limitations

- **Synchronous processing** — analysis, correlation, and RCA run in the API request; large uploads may hit `ANALYSIS_MAX_LOGS`, `CLUSTER_MAX_LOGS`, `RCA_MAX_LOGS`.
- **Single-instance rate limiting** — counters are in-memory; multiple replicas need edge limits or shared state (not in scope).
- **JWT logout** — no server-side token blacklist.
- **Ollama** — optional narrative enhancement only; disabled by default.
- **Log storage** — filesystem default; production requires a mounted volume; S3 backend flag is reserved, not fully implemented.
- **Isolation Forest / DBSCAN** — CPU-bound; tuned for laptop-scale data, not petabyte logs.
- **RCA scores** — heuristic rankings, not calibrated probabilities.
- **Incident correlation** — temporal/service heuristics; does not prove causation.
- **CSRF** — Bearer-token clients skip Origin checks; cookie clients require matching Origin.
- **No multi-tenant org model** — isolation is per-user project ownership only.