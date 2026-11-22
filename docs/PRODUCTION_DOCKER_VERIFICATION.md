# Production Docker Verification — PulseTrace

**Verification date:** 2026-11-22
**Isolated project name:** `pulsetrace-prod-qa`
**Migration head verified in container:** `d7e8f9a0b1c2`

## Executive summary

An **isolated** production-style stack was built and exercised on a Windows host with Docker Desktop. The development Postgres container (`pulsetrace-postgres` on port **5433**) and its volume were **not** modified.

**Genuine issues fixed before/during verification:**

1. **Nginx returned 404 for `/api/`** — blocked same-origin production deployments. **Fixed:** reverse proxy to `backend:8000`.
2. **Frontend API URL baked to cross-origin `localhost:8000`** — brittle cookies in prod Compose. **Fixed:** empty `VITE_API_BASE_URL` + `resolveApiBaseUrl()` for same-origin `/api/v1`.
3. **`docker-compose.prod.yml` lacked backend healthcheck** and frontend started before API was ready. **Fixed:** healthchecks + `depends_on: condition: service_healthy`.
4. **Fixed `container_name` in prod compose conflicts** with dev when both run — **mitigated** via separate `docker-compose.prod.qa.yml` (no fixed container names, ports **5434 / 8001 / 8081**).

**Isolated stack result:** **PASS** for build, health, migrations, nginx proxy, SPA, same-origin Playwright workflow, upload/log persistence after backend restart.

**Not verified:** public cloud deploy, TLS termination, `AUTH_COOKIE_SECURE=true` behind HTTPS (documented only).

## Files inspected

| File | Notes |
|------|--------|
| `docker-compose.prod.yml` | Updated healthchecks, same-origin build arg |
| `docker-compose.prod.qa.yml` | **New** — isolated QA stack |
| `backend/Dockerfile` | Non-root user, entrypoint migrations |
| `backend/scripts/docker-entrypoint.sh` | DB wait + `alembic upgrade head` |
| `frontend/Dockerfile` | Multi-stage build + nginx |
| `frontend/nginx.conf` | SPA + `/api/` proxy |
| `deploy/pulsetrace-prod-qa.env.example` | QA env template |
| `backend/app/core/production.py` | Startup validation |

## Isolation details

| Resource | Development (unchanged) | QA verification |
|----------|-------------------------|-----------------|
| Compose project | default / dev | `pulsetrace-prod-qa` |
| Postgres container | `pulsetrace-postgres` | `pulsetrace-prod-qa-postgres-1` |
| DB name | `pulsetrace` (dev) | `pulsetrace_qa` |
| Volumes | `pulsetrace_pulsetrace_pgdata` | `pulsetrace-prod-qa_pgdata_qa`, `pulsetrace-prod-qa_uploads_qa` |
| Env file | `.env` (not touched) | `deploy/pulsetrace-prod-qa.env` (gitignored) |
| Host ports | 5433 | 5434, 8001, 8081 |

## Reproduce the isolated stack

```powershell
cd C:\Users\Dhanv\Downloads\pulsetrace

# 1. Create secrets file from example (do not commit)
Copy-Item deploy\pulsetrace-prod-qa.env.example deploy\pulsetrace-prod-qa.env
# Edit: set POSTGRES_PASSWORD and JWT_SECRET_KEY (>= 32 bytes hex)

# 2. Build and start
docker compose -p pulsetrace-prod-qa -f docker-compose.prod.qa.yml `
  --env-file deploy/pulsetrace-prod-qa.env up --build -d

# 3. Health
Invoke-RestMethod http://127.0.0.1:8081/api/v1/health/database
Invoke-RestMethod http://127.0.0.1:8001/api/v1/health/database

# 4. Playwright (nginx same-origin)
cd frontend
$env:E2E_PROD_STACK="1"
$env:E2E_SKIP_WEBSERVER="1"
$env:E2E_BASE_URL="http://127.0.0.1:8081"
npm run test:e2e -- prod-docker.spec.ts

# 5. Persistence scripts
cd ..
backend\.venv\Scripts\python.exe scripts\qa_prod_persist_check.py
docker compose -p pulsetrace-prod-qa -f docker-compose.prod.qa.yml `
  --env-file deploy/pulsetrace-prod-qa.env restart backend
backend\.venv\Scripts\python.exe scripts\qa_prod_persist_verify.py

# Teardown (QA only — no -v unless you intend to delete QA volumes)
docker compose -p pulsetrace-prod-qa -f docker-compose.prod.qa.yml down
```

## Verification matrix

| Item | Result | Evidence |
|------|--------|----------|
| Postgres healthy before backend | **PASS** | Compose `service_healthy` gate |
| Backend waits for DB (entrypoint) | **PASS** | `docker-entrypoint.sh` wait loop |
| Alembic `upgrade head` on start | **PASS** | `alembic current` → `d7e8f9a0b1c2` in QA container |
| Backend healthcheck | **PASS** | Container status `healthy` |
| Nginx serves SPA | **PASS** | `GET /login` → 200 |
| Nginx proxies `/api/v1/*` | **PASS** | Health via `http://127.0.0.1:8081/api/v1/health/database` |
| SPA nested route refresh | **PASS** | Playwright `prod-docker.spec.ts` |
| Same-origin auth + full workflow | **PASS** | Playwright prod-docker (register → RCA → logout) |
| Production disables `/docs` | **PASS** | `GET :8001/docs` → 404 |
| Upload + log DB persistence after backend restart | **PASS** | `scripts/qa_prod_persist_*.py` |
| Postgres restart + data retained | **PASS** | Implicit via persist verify after earlier postgres restart |
| Frontend restart / recovery | **NOT VERIFIED** | Not restarted in this session |
| Backend unavailability UX | **NOT VERIFIED** | No dedicated test |
| TLS + `AUTH_COOKIE_SECURE=true` | **NOT VERIFIED** | HTTP QA only |
| Cloud deployment | **NOT VERIFIED** | No hosted URL |

## Test results (before → after)

| Suite | Before | After (this session) |
|-------|--------|----------------------|
| Backend pytest | 63 | **66** (+3 `test_docker_compose.py`) |
| Frontend Vitest | 15 | **16** (+`api-base.test.ts`) |
| Playwright (dev API) | 27 | **27** (not re-run here) |
| Playwright prod-docker | — | **2 passed** |
| Frontend build | OK | **OK** |
| Isolated prod Compose | Not run | **Build + up PASS** |

## Regression tests added

- `backend/tests/test_docker_compose.py` — nginx proxy, QA compose isolation, healthchecks
- `frontend/src/test/api-base.test.ts` — same-origin API base URL
- `frontend/e2e/prod-docker.spec.ts` — nginx stack workflow (requires `E2E_PROD_STACK=1`)
- `scripts/qa_prod_persist_check.py` / `qa_prod_persist_verify.py` — upload persistence after restart

## Remaining limitations

- In-memory rate limits (single backend instance).
- JWT not revoked until expiry.
- `AUTH_COOKIE_SECURE=false` in local HTTP QA; enable with HTTPS reverse proxy.
- Backend port **8001** still exposed on host for debugging; omit in true production edge deploy.
- No automatic Playwright prod job in GitHub Actions yet (optional follow-up).

## Commands executed (this verification)

- `docker compose -p pulsetrace-prod-qa -f docker-compose.prod.qa.yml --env-file deploy/pulsetrace-prod-qa.env build`
- `docker compose ... up -d`
- HTTP health via PowerShell / Python urllib
- `npm run test:e2e -- prod-docker.spec.ts` with `E2E_PROD_STACK=1`
- `scripts/qa_prod_persist_check.py` / `qa_prod_persist_verify.py`
- `docker compose ... restart backend` (and postgres once)
- `pytest`, `npm test`, `npm run build`
