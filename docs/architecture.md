# PulseTrace Architecture

## Overview

PulseTrace is built as a **modular monolith**: a single deployable application with clear internal boundaries so future capabilities can grow without premature microservice sprawl.

```
┌─────────────────────────────────────────────────────────────┐
│                        PulseTrace                           │
├──────────────────────────┬──────────────────────────────────┤
│   Frontend (React SPA)   │   Backend (FastAPI)              │
│   - Dashboard shell      │   - HTTP API /api/v1             │
│   - Feature modules      │   - Core config & logging        │
│   - API client layer     │   - DB session & repositories    │
└──────────────────────────┴──────────────────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │  PostgreSQL 16  │
                            └─────────────────┘
```

## Phase 1 (Complete)

- **Frontend**: Dark-mode dashboard shell, routing placeholders, honest empty states.
- **Backend**: Bootstrap, structured logging, CORS, versioned health endpoints, DB connectivity via SQLAlchemy 2.0.

## Phase 2 (Current)

- **Database**: Alembic migrations; `users`, `projects`, `services` tables (services are registered but not yet exposed via API UI).
- **Auth**: Argon2 password hashing, JWT access tokens, HttpOnly session cookie for browser clients, Bearer token support for tests/API clients.
- **Projects**: Authenticated CRUD scoped to `owner_id` from JWT subject (no client-supplied owner).
- **Frontend**: Login/register, protected routes, projects list/detail with TanStack Query against live endpoints.

### Authentication flow (browser)

1. `POST /api/v1/auth/login` validates credentials and sets an HttpOnly cookie (`pulsetrace_access_token`).
2. SPA calls use `fetch(..., { credentials: "include" })` with CORS `allow_credentials`.
3. `GET /api/v1/auth/me` resolves the current user from cookie or `Authorization: Bearer`.
4. JWT secret and cookie flags are environment-driven (`JWT_SECRET_KEY`, `AUTH_COOKIE_*`).
5. Tokens are not stored in `localStorage` by the frontend.

## Phase 3 (Complete)

- **Ingestion**: Multipart upload (`/projects/{id}/logs/upload`) for CSV, JSON, JSONL, TXT with streaming disk storage under `LOG_STORAGE_PATH`.
- **Processing**: Modular normalization pipeline in `app/modules/logs/` (timestamps → UTC, level aliases, field mapping, deterministic SHA-256 fingerprints).
- **Persistence**: `log_batches` tracking + `logs` table with JSONB metadata; batched inserts (`LOG_INSERT_BATCH_SIZE`).
- **Query**: Filterable, paginated search scoped to project ownership; batch listing/detail endpoints.
- **Services API**: Read/create project services for upload filters and name-based association.

## Phase 4 (Complete)

- **Anomaly persistence**: `anomalies` table with JSONB `evidence`, severity, dedupe keys to avoid duplicate records on re-analysis.
- **Clustering persistence**: `log_clusters` + `log_cluster_memberships` (rebuilt per analysis run).
- **Detection modules** (`app/modules/anomaly_detection/`):
  - Feature extraction into time buckets (`features.py`).
  - Statistical z-score rules (`statistical.py`) — distinct from ML; documented in evidence.
  - Isolation Forest on scaled numeric features (`isolation_forest.py`).
- **Clustering module** (`app/modules/clustering/`): message normalization + TF-IDF + DBSCAN; explicitly text-similarity, not semantic NLU.
- **Orchestration** (`app/modules/analysis/runner.py`): batch-oriented project/service analysis; not hooked to per-log inserts.
- **API**: `POST .../analysis/run`, `GET .../anomalies`, `GET .../clusters` (filters + pagination); all routes use `get_owned_project`.
- **Frontend**: Anomaly hub, dashboard (run + severity chart), explorers with evidence JSON and cluster member logs.

### Severity rules (summary)

| Condition | Severity |
|-----------|----------|
| `critical_count >= 5` or critical spike z ≥ 4 | CRITICAL |
| Any critical, or `error_count >= 20`, or z ≥ 3.5 | HIGH |
| `error_count >= 5`, or z ≥ 2.5, or IF score > 0.65 | MEDIUM |
| Otherwise | LOW |

### Limitations

- Analysis window and row caps are configurable but still in-process (no Celery/Redis).
- Clustering quality depends on TF-IDF cosine similarity; paraphrases may not group.
- Isolation Forest requires sufficient bucket rows (`ANALYSIS_IF_MIN_ROWS`).

## Phase 5 (Complete)

- **Models**: `incidents`, `incident_events`, `incident_evidence`, `deployments`, `service_dependencies`.
- **Correlation** (`app/modules/incidents/correlator.py`): union-find grouping on unlinked anomalies; merges into active incidents by time/service; cluster overlap edges; deployment timeline events with explicit non-causation wording.
- **Severity** (`severity.py`): documented aggregation from linked anomaly severities.
- **Lifecycle**: manual create, PATCH status (resolve/reopen), investigation notes as timeline events.
- **Config**: `INCIDENT_CORRELATION_*`, `INCIDENT_DEPLOYMENT_WINDOW_MINUTES`.

## Phase 6 (Current)

- **Models**: `rca_investigations` (versioned per incident), `root_cause_candidates` with JSONB evidence summaries.
- **Pipeline** (`app/modules/root_cause/`): collect → generate candidates → score → rank → persist → report.
- **Scoring**: `100 * support / (support + contradict + ε)` with per-category weights (`RCA_WEIGHT_*`) and deduped evidence keys.
- **Reports**: structured JSON + Markdown; optional Ollama narrative is off by default and not required.
- **Principle**: ranks plausible hypotheses from stored records; never claims proven causation.

## Backend layout

| Area | Responsibility |
|------|----------------|
| `app/core/` | Settings, logging, cross-cutting configuration |
| `app/db/` | Engine, session factory, FastAPI dependencies |
| `app/api/v1/` | Versioned HTTP surface and routers |
| `app/models/` | SQLAlchemy models (Phase 2+) |
| `app/schemas/` | Pydantic request/response models |
| `app/repositories/` | Data access (Phase 2+) |
| `app/modules/logs/` | Ingestion, normalization, fingerprints |
| `app/modules/anomaly_detection/` | Bucketing, z-score, Isolation Forest |
| `app/modules/clustering/` | Text normalize, TF-IDF, DBSCAN |
| `app/modules/analysis/` | Severity rules, orchestration runner |

## Planned modules (Phase 5+)

1. **Incident management** — lifecycle linked to anomalies.
2. **Service catalog & health** — dependencies and SLO-oriented status.
3. **Deployment correlation** — tie releases to failure windows.
4. **Investigations & RCA** — evidence graph and hypotheses.
5. **Authentication & tenancy** — organizations, RBAC, API keys.

Each module should expose routes under `/api/v1/...`, use repositories for persistence, and publish events or hooks only when cross-module coupling is required.

## Design principles

- **Environment-based configuration** — no hardcoded secrets; `DATABASE_URL` and CORS from settings.
- **API versioning** — breaking changes ship under new prefixes (`/api/v2`), not silent breaks.
- **Empty over fake** — UI and APIs return honest empty/unconfigured states until data sources are connected.
- **Testability** — health and DB checks are integration-friendly; unit tests avoid live infrastructure where possible.

## Frontend layout

- `components/ui` — primitives (buttons, cards, inputs).
- `components/layout` — shell (sidebar, header).
- `components/common` — empty states, placeholders.
- `features/*` — route-aligned feature folders (Phase 1: `dashboard` only).
- `services/` — HTTP client and TanStack Query hooks.

Routing uses React Router; server state will use TanStack Query as features gain real endpoints.

## Phase 7 (Complete)

- **Production guardrails**: `validate_production_settings()`, sanitized 500 errors, security headers, CSRF Origin check for cookie auth, in-process rate limits.
- **Containers**: `backend/Dockerfile`, `frontend/Dockerfile` + nginx SPA fallback, `docker-compose.prod.yml` with Postgres + upload volume.
- **Demo**: `scripts/seed_demo.py` (ShopFlow synthetic scenario via ingestion pipeline).
- **CI**: `.github/workflows/ci.yml` (Postgres service, pytest, Vitest, frontend build).
- **Docs**: deployment, security, backup, demo walkthrough, portfolio guide, known limitations.