# API Reference (v1)

Base path: `/api/v1`
Interactive OpenAPI: `/docs` (disabled when `APP_ENV=production`).

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | JWT + optional HttpOnly cookie |
| POST | `/auth/logout` | Clear session cookie |
| GET | `/auth/me` | Current user |

Use `Authorization: Bearer <token>` or session cookie (`credentials: include`).

## Projects

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/projects` | List / create |
| GET/PATCH/DELETE | `/projects/{id}` | Detail / update / delete |

## Services

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/projects/{id}/services` | List / create |
| POST | `/projects/{id}/services/dependencies` | Dependency edge |

## Logs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/{id}/logs/upload` | Multipart file upload |
| GET | `/projects/{id}/logs` | Search / filter |
| GET | `/projects/{id}/logs/batches` | Upload batches |

## Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/{id}/analysis/run` | Run anomaly + cluster pipeline |
| GET | `/projects/{id}/anomalies` | List anomalies |
| GET | `/projects/{id}/clusters` | List clusters |

## Incidents

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/projects/{id}/incidents` | List / create |
| POST | `/projects/{id}/incidents/correlate` | Auto-correlate from anomalies |
| GET | `/projects/{id}/incidents/{incident_id}` | Detail |
| GET | `/projects/{id}/incidents/{incident_id}/timeline` | Timeline events |
| POST | `/projects/{id}/incidents/{incident_id}/investigate` | Run RCA |
| GET | `/projects/{id}/incidents/{incident_id}/investigation-report` | JSON report |
| GET | `/projects/{id}/incidents/{incident_id}/investigation-report.md` | Markdown export |
| POST | `/projects/{id}/incidents/deployments` | Record deployment |

All `{id}` routes enforce **project ownership** via authenticated user.

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Root health |
| GET | `/api/v1/health` | API health |
| GET | `/api/v1/health/database` | DB connectivity |
