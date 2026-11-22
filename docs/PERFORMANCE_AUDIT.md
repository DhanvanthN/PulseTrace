# Performance Audit

PulseTrace targets **laptop-scale** workloads with explicit env caps (`ANALYSIS_MAX_LOGS`, `CLUSTER_MAX_LOGS`, `RCA_MAX_LOGS`). No load-testing cluster was used.

## Measurements taken (2026-11-20, local)

| Operation | Wall time | Environment |
|-----------|-----------|-------------|
| Full backend pytest (63 tests) | ~57 s | Windows, Postgres on 5433 |
| ShopFlow `analysis/run` (re-run) | ~0.96 s | TestClient, existing demo data |
| Frontend `npm run build` | ~20 s | Vite 5 |
| Playwright smoke (3 tests) | ~4 s | Chromium, dev server |

## Architectural limits

- Analysis, correlation, and RCA run **synchronously** in the HTTP request thread.
- Log ingestion streams to disk; DB inserts batched (`LOG_INSERT_BATCH_SIZE`).
- Overview dashboard issues parallel queries per project (acceptable for few projects).

## N+1 review (sample)

- Project-scoped list endpoints use repository queries with limits.
- RCA evidence collection loads bounded sets (`RCA_MAX_LOGS`).

No N+1 regressions were fixed in this campaign because none were measured as user-visible defects.

## Recommendations (future)

- Background job queue for analysis/RCA at scale.
- Project-level overview aggregation endpoint to reduce frontend fan-out.
- Query timing logs in production (optional OpenTelemetry).

Do **not** cite throughput or latency as SLA figures — samples above are indicative only.