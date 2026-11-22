# Portfolio and Interview Guide

This guide lets reviewers **understand and evaluate PulseTrace without screenshots or a public deployment**. Evidence of quality: runnable demo, tests, OpenAPI (dev), and documentation in this repo.

## Written project presentation (for README, LinkedIn, or reviewers)

### Elevator pitch

PulseTrace turns uploaded application logs into **anomalies**, **correlated incidents**, and **ranked root-cause hypotheses** backed by explicit supporting and contradicting evidence—with Markdown investigation reports suitable for post-incident review.

### What you built end-to-end

- **Frontend:** Dark observability UI (dashboard, log explorer, analysis, incident workspace, RCA with evidence strength labeling).
- **Backend:** Versioned REST API, modular pipelines for ingestion, stats/ML detection, correlation, and deterministic RCA.
- **Data:** PostgreSQL schema with Alembic migrations; filesystem persistence for raw uploads.
- **Ops:** Dockerfiles, compose stacks, GitHub Actions CI, security middleware, ShopFlow demo seed via real ingestion.

### How to demo in 10 minutes (no images needed)

1. Start Postgres + API + SPA (see root [README](../README.md)).
2. Run `scripts/seed_demo.py` with `--create-demo-user` (once).
3. Sign in → open **ShopFlow (Demonstration)**.
4. Run **analysis** → **correlate** → open incident → **Run RCA investigation** → **Export Markdown**.

Narration points: scores are **evidence strength**, deployments are **temporal context only**, correlation ≠ causation.

## Project description (resume / LinkedIn)

PulseTrace is a full-stack observability and incident investigation platform that ingests structured logs, detects anomalies, correlates incidents across services, and produces ranked, evidence-based root cause hypotheses with exportable investigation reports.

## Resume bullets

- Built a modular monolith (React, FastAPI, PostgreSQL) for log ingestion, time-series anomaly detection (z-score + Isolation Forest), and TF-IDF/DBSCAN error clustering with configurable resource limits for laptop-scale deployments.
- Implemented multi-tenant project isolation with Argon2 + JWT auth, ownership checks on all project-scoped APIs, and production middleware (CORS, CSRF Origin checks, rate limiting, sanitized errors).
- Designed incident correlation and deterministic RCA scoring that combines deployment timing, service dependencies, and contradictory evidence — without requiring an LLM.
- Delivered Docker-based production packaging, Alembic migrations, GitHub Actions CI configuration (66 backend + 16 frontend + 27 Playwright E2E tests verified locally), and a repeatable ShopFlow demo dataset seeded through the real ingestion pipeline.

## Screenshots (optional)

Real E2E captures live in [screenshots/e2e/](./screenshots/e2e/) (dashboard, incidents, RCA). Do not use mock or AI-generated UI images as evidence of the product.

## Interview questions

### 1. What problem does PulseTrace solve?

On-call engineers drown in raw logs. PulseTrace narrows volume into anomalies, grouped incidents, and testable root-cause hypotheses with cited evidence.

### 2. Why a modular monolith?

Single deployable unit fits portfolio scale and a 16 GB laptop. Modules (`logs`, `analysis`, `incidents`, `root_cause`) bound complexity without operational overhead of microservices.

### 3. Why PostgreSQL?

Relational ownership model, JSONB for evidence metadata, mature migrations (Alembic), and one database for auth through RCA.

### 4. How does log ingestion work?

Multipart upload → sanitize filename → stream to disk → parse CSV/JSON/JSONL/TXT → normalize timestamps/levels → map service names → fingerprint → batch insert.

### 5. How does anomaly detection work?

Logs aggregate into time buckets; statistical rules flag spikes; Isolation Forest runs on scaled numeric features when enough samples exist.

### 6. Why Isolation Forest?

Unsupervised, handles multivariate bucket features, reasonable CPU cost vs deep learning; contamination parameter documents assumptions.

### 7. How does TF-IDF clustering work?

Error messages are normalized (strip IDs/IPs); TF-IDF vectors feed DBSCAN to group similar messages — similarity is lexical, not semantic embeddings.

### 8. How are incidents correlated?

Heuristics over time windows, shared services, dependency graph edges, and cluster overlap — deduplicated; correlation is not causation.

### 9. How does RCA scoring work?

Weighted evidence types (temporal, deployment proximity, service match, dependency path, patterns); contradictions apply penalties; candidates ranked by total score.

### 10. Contradictory evidence?

Explicit contradicting items reduce confidence (e.g., errors before deployment undermines “bad deploy” narratives).

### 11. Why aren't RCA scores probabilities?

Scores are comparative rankings from weighted heuristics — not trained on labeled incidents; stating probabilities would be misleading.

### 12. Multi-user data isolation?

Every project has `owner_id`; APIs resolve project via JWT user; other users receive 404 on foreign IDs.

### 13. Log volume growth?

Caps (`ANALYSIS_MAX_LOGS`, etc.), pagination, synchronous processing — would add background jobs and sampling next at scale.

### 14. Limitations?

See [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md).

### 15. What would you improve next?

Background job queue for analysis, JWT refresh/rotation, distributed rate limits, and—only if needed—object storage with a real S3-compatible implementation (today: filesystem only). Do not claim cloud deploy until you have verified your own hosting URL.

## What this project does **not** claim

- No production cloud URL unless you deploy and verify it yourself.
- No Amazon S3 (or other object store) integration in code—only filesystem uploads.
- No LLM-required RCA (Ollama optional and disabled by default).