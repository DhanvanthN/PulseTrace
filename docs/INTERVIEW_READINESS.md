# Interview Readiness Checklist

Use with `docs/PORTFOLIO_AND_INTERVIEW_GUIDE.md`.

## Demonstrable in 10 minutes

1. `docker compose up -d` + `alembic upgrade head`
2. `scripts/seed_demo.py --create-demo-user` (once)
3. UI: ShopFlow → analysis → correlate → incident → **Run RCA** → export Markdown
4. Show evidence strength labels (not probabilities)

## Technical topics — answerable from code/docs

| # | Topic | Where to look |
|---|--------|----------------|
| 1 | Architecture | `docs/architecture.md` |
| 2 | FastAPI choice | Modular routers, Pydantic, OpenAPI |
| 3 | PostgreSQL | JSONB evidence, ownership, Alembic |
| 4 | React/TS | Typed API layer, TanStack Query |
| 5 | Modular monolith | `app/modules/*` boundaries |
| 6 | DB relationships | `users` → `projects` → logs/incidents/RCA |
| 7 | JWT + Argon2 | `app/core/security.py`, `auth.py` |
| 8 | Log ingestion | `app/modules/logs/` |
| 9 | Statistical anomalies | `app/modules/anomaly_detection/statistical.py` |
| 10 | Isolation Forest | `isolation_forest.py`, env contamination |
| 11 | TF-IDF + DBSCAN | `app/modules/clustering/` |
| 12 | Incident correlation | `app/modules/incidents/correlator.py` |
| 13 | Temporal union-find | **Clarify:** correlator uses heuristics/overlap, not formal union-find — describe honestly |
| 14 | RCA evidence collection | `evidence_collector.py` |
| 15 | RCA scoring | `evidence_scorer.py`, weights in `.env.example` |
| 16 | Contradicting evidence | Penalty in scorer; UI splits stances |
| 17 | Scores ≠ probabilities | `score_note` in API + UI |
| 18 | Migrations | Alembic chain, head `d7e8f9a0b1c2` |
| 19 | Docker | `backend/Dockerfile`, `docker-compose.prod.yml` |
| 20 | Security middleware | Phase 7 `main.py` middleware stack |
| 21 | Performance limits | Sync jobs + env caps |
| 22 | Trade-offs | `KNOWN_LIMITATIONS.md` |
| 23 | Future work | Async jobs, optional object storage **implementation** |

## Proof artifacts

| Artifact | Status |
|----------|--------|
| 66 backend tests | Verified passing (local) |
| 16 frontend unit tests | Verified passing (local) |
| 27 Playwright E2E tests | Verified passing (local; prod-docker optional +2) |
| GitHub Actions green | **Pending** — workflow configured, first remote run not verified |
| No cloud deploy URL | Honest — not claimed |

## Gaps to rehearse

- Explain **correlation ≠ causation** and deployment timeline caveats.
- Explain why **ShopFlow demo email** uses `pulsetrace` domain but E2E uses `@example.com` (Pydantic email validation).