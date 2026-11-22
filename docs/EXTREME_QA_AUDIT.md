# Extreme QA Audit — PulseTrace

**Campaign date:** 2026-11-20
**Repository:** `C:\Users\Dhanv\Downloads\pulsetrace`

## Phase 1 baseline (verified)

| Check | Before campaign | After campaign |
|-------|-----------------|----------------|
| Backend pytest | 59 passed | **63 passed** |
| Frontend Vitest | 15 passed | **15 passed** |
| Frontend build | Success | **Success** |
| Playwright E2E | 3 smoke tests | **27 passed** (full workflow suite) |
| Alembic head | `d7e8f9a0b1c2` | **unchanged** |

## Issues discovered and severity

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| Q1 | **Medium** | Cross-user IDOR tests missing for logs/incidents/RCA | **Fixed** — `test_security_isolation.py` |
| Q2 | **Medium** | `resolve_stored_upload_path` unused; path traversal helper not exercised | **Fixed** — helper + unit test |
| Q3 | **Low** | Global `Exception` handler could shadow validation errors | **Fixed** — explicit `RequestValidationError` handler |
| Q4 | **Low** | RCA UI generic error on investigation failure | **Fixed** — surface `ApiError` message |
| Q5 | **Medium** | No browser-level E2E automation | **Fixed** — Playwright smoke suite |
| Q6 | **Low** | E2E register used `.local` emails rejected by API | **Fixed** — `@example.com` + Bearer route injection |
| Q11 | **Low** | Vitest collected `e2e/smoke.spec.ts` and failed suite | **Fixed** — `vite.config.ts` `test.exclude: e2e/**` |
| Q12 | **Medium** | Duplicate `/investigations` nav key caused React warnings in E2E | **Fixed** — removed disabled Deployments duplicate |
| Q13 | **Low** | Logout did not navigate to sign-in | **Fixed** — `Header` navigates after logout |
| Q14 | **Low** | Log detail panel had no loading/error UI; `Card` dropped `data-testid` | **Fixed** — explorer UX + `Card` spreads HTML attrs |
| Q15 | **Low** | Log row click unreliable in automation | **Fixed** — per-row **View** button |
| Q16 | **Info** | E2E suite expanded (auth → RCA, 5 viewports) | **Done** — see `frontend/e2e/*.spec.ts` |
| Q17 | **Info** | Playwright only ran locally | **Fixed** — `ci.yml` job `Playwright E2E` (27 tests, isolated DB) |
| Q7 | **Low** | Dev dependency advisories (esbuild/vitest moderate) | **Open** — breaking upgrade deferred |
| Q8 | **Low** | Cross-port HttpOnly cookie auth brittle in real browsers | **Documented** — login UI path works; E2E uses Bearer injection |
| Q9 | **Info** | `LOG_STORAGE_BACKEND=s3` unused | **Documented** — filesystem only |
| Q10 | **Info** | `docker-compose.prod.yml` not executed in prior campaign | **Verified** — isolated `pulsetrace-prod-qa` stack 2026-11-22; see `docs/PRODUCTION_DOCKER_VERIFICATION.md` |

No **Critical** or **High** defects found in automated runs.

## Issues reproduced

- Q6 reproduced via Playwright error context (Pydantic email validation).
- Q1 reproduced by inspection (missing tests); verified fix returns 404 for cross-user access.

## Fixes applied (code)

- `backend/app/modules/logs/storage.py` — `resolve_stored_upload_path()`
- `backend/app/main.py` — `RequestValidationError` handler
- `backend/tests/test_security_isolation.py` — new (4 tests)
- `frontend/e2e/*` — Playwright config + smoke tests
- `frontend/package.json` — `@playwright/test`, `test:e2e` script
- `frontend/src/features/incidents/IncidentRcaSection.tsx` — investigation error text
- `.gitignore` — Playwright artifacts
- `frontend/vite.config.ts` — exclude `e2e/**` from Vitest
- `README.md` — doc index + test counts
- `docs/*.md` — audit deliverables (this file, TESTING_GUIDE, SECURITY_AUDIT, PERFORMANCE_AUDIT, INTERVIEW_READINESS)

## Performance samples (single machine, not benchmarks)

| Operation | Measured | Notes |
|-----------|----------|--------|
| `POST .../analysis/run` (ShopFlow demo) | **~0.96 s** | TestClient, env=test, existing logs |
| Backend pytest suite | **~57 s** | 63 tests, local Postgres |
| Frontend Vitest | **~15 s** | 15 tests |
| Playwright E2E | **~1.6 min** | 27 tests, serial worker, real API |

## Security testing summary

- Ownership: `get_owned_project` on scoped routes; new IDOR regression tests pass.
- Auth: existing tests cover duplicate register, bad login, expired/invalid JWT.
- Path traversal: unit test on `resolve_stored_upload_path`.
- Rate limit / CSRF / production validation: covered by `test_production.py` + middleware (in-process limits only).

## CI verification

| Check | Status |
|-------|--------|
| `ci.yml` YAML parse (local) | **Passed** |
| Playwright 27/27 (local, Win11 + Postgres) | **Passed** (after CI config change) |
| GitHub Actions `Playwright E2E` job on `ubuntu-latest` | **Not executed in this session** — requires push/PR to GitHub |

E2E CI job: Postgres 16 service → Alembic → uvicorn → Vitest → build → `playwright install --with-deps chromium` → full suite → artifacts (report, test-results, screenshots, uvicorn log on failure).

## Deployment verification

- **Not executed:** `docker compose -f docker-compose.prod.yml up --build`
- Dockerfiles and nginx config reviewed; no syntax issues found.

## Remaining limitations

See `docs/KNOWN_LIMITATIONS.md`. Synchronous pipelines, no S3, no JWT revocation, single-instance rate limits.

## Commands executed (this campaign)

```text
backend: pytest -q
frontend: npm test -- --run
frontend: npm run build
frontend: npm run test:e2e
.github/workflows/ci.yml: YAML validated (PyYAML)
frontend: npm audit --audit-level=high
backend: alembic current
```
