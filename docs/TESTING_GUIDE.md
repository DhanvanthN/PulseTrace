# Testing Guide

## Backend (pytest)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head   # requires Postgres
pytest -q
```

**Count (2026-11-22):** **66** tests (includes `test_docker_compose.py`) across auth, projects, logs, analysis, incidents, RCA, production, security isolation, health.

Requires `DATABASE_URL` (default port **5433** in `.env.example`). Uses `APP_ENV=test` in `conftest.py`.

### Notable suites

| File | Focus |
|------|--------|
| `test_security_isolation.py` | Cross-user 404 on logs, analysis, incidents, RCA |
| `test_rca.py` | Deterministic scoring, contradiction penalty |
| `test_production.py` | Production JWT validation rules |

## Frontend unit tests (Vitest)

```powershell
cd frontend
npm test -- --run
```

**Count:** **16** tests (includes `api-base.test.ts`) (RTL + mocked fetch). Vitest **excludes** `e2e/**`.

## Frontend production build

```powershell
cd frontend
npm run build
```

Runs `tsc --noEmit` then Vite production bundle.

## Browser E2E (Playwright)

**Prerequisites:** Postgres running, migrations applied, backend on `http://127.0.0.1:8000` (or set `E2E_API_URL`).

For a **full local suite** (many register/login calls), start the API with **`APP_ENV=test`** so in-process auth rate limiting is disabled—the same as the GitHub Actions E2E job. With `APP_ENV=development` and the default `RATE_LIMIT_AUTH_PER_MINUTE=20`, long runs can return HTTP **429** near the end of the suite.

```powershell
cd backend
$env:APP_ENV="test"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
# separate terminal:
cd frontend
npm run test:e2e
```

Playwright starts Vite on **5173** with `VITE_API_BASE_URL` aligned to `E2E_API_URL`. Tests run **serially** (`workers: 1`) for stable DB isolation.

**Count (verified 2026-11-22):** **27** executed tests in a default run (**29** listed; **2** `prod-docker` tests skip unless `E2E_PROD_STACK=1`) across **10** spec files.

| Spec | Coverage |
|------|-----------|
| `auth.spec.ts` | Register, login, logout, protected routes, session expiry |
| `projects.spec.ts` | Empty state, create, list, switch, detail |
| `logs.spec.ts` | Upload validation, UI upload, explorer search/filter/pagination, detail |
| `analysis.spec.ts` | Run analysis, anomalies, clusters, empty project |
| `incidents.spec.ts` | Correlate, explorer, timeline, notes, resolve/reopen, deployments |
| `rca.spec.ts` | Investigation, evidence strength, report, Markdown export |
| `responsive.spec.ts` | 360–1920px layouts, horizontal overflow, RCA panel |
| `workflows.spec.ts` | Full ingest → analyze → correlate → RCA path |
| `smoke.spec.ts` | API health + login shell |

### E2E data isolation

Each test uses a unique `e2e-pulsetrace-*@example.com` user via `PulseTraceApi` helpers (`e2e/helpers/api.ts`). Deterministic JSONL spike mirrors backend `test_analysis._recent_jsonl_spike`. No manual DB cleanup; no destructive operations.

### E2E auth note

Cross-origin HttpOnly cookies (`5173` → `8000`) are brittle in automation. Tests inject `Authorization: Bearer` via `page.route` for API calls. UI login/register tests also capture the JWT from the login response body.

### Screenshots

On success, selected tests write **real** captures to `docs/screenshots/e2e/` (see `docs/screenshots/e2e/README.md`).

## Production Docker E2E (optional)

When the **isolated QA stack** is running (`docker-compose.prod.qa.yml`):

```powershell
cd frontend
$env:E2E_PROD_STACK="1"
$env:E2E_SKIP_WEBSERVER="1"
$env:E2E_BASE_URL="http://127.0.0.1:8081"
npm run test:e2e -- prod-docker.spec.ts
```

Persistence checks: `scripts/qa_prod_persist_check.py` and `scripts/qa_prod_persist_verify.py`. See [PRODUCTION_DOCKER_VERIFICATION.md](PRODUCTION_DOCKER_VERIFICATION.md).

## CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml`

| Job | What it runs |
|-----|----------------|
| `backend` | Postgres service → Alembic → **66** pytest tests |
| `frontend` | `npm ci` → Vitest → production build |
| `Playwright E2E` | Dedicated Postgres DB (`pulsetrace_e2e`) → migrations → uvicorn → Vitest → build → Playwright Chromium → **27** E2E tests |

E2E job environment (no `.env` file on runner):

- `DATABASE_URL=postgresql+psycopg://pulsetrace:ci_test_password@localhost:5432/pulsetrace_e2e`
- `JWT_SECRET_KEY` — fixed test value (not production)
- `LOG_STORAGE_PATH=/tmp/pulsetrace-e2e-uploads`
- `E2E_API_URL=http://127.0.0.1:8000`, `E2E_BASE_URL=http://127.0.0.1:5173`

Artifacts (uploaded **even when tests fail**, 14-day retention):

- `playwright-report` — HTML report
- `playwright-test-results` — traces/screenshots on failure
- `playwright-e2e-screenshots` — `docs/screenshots/e2e/` captures from passing flows
- `e2e-uvicorn-log` — API log (failures only)

Playwright uses `workers: 1`, `retries: 1` when `CI=true`, and does **not** reuse an existing Vite server on CI.

## What is not automated

- Production Docker stack bring-up
- Load/concurrency testing at scale
- Full keyboard-only accessibility audit (partial coverage via Playwright roles/labels)