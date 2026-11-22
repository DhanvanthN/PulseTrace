# Security

## Authentication

- Passwords hashed with **Argon2** (`app.core.security`).
- Access tokens are **JWT** (HS256); expiry from `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.
- Optional **HttpOnly** cookie (`AUTH_COOKIE_NAME`) with `SameSite` and `Secure` flags.

### Limitations

- JWTs are **not revocable** server-side until expiry; logout clears client cookie only.
- Use short TTL and HTTPS in production.

## Authorization

- Project-scoped routes depend on `get_owned_project` — cross-user project IDs return 404.
- Log batches, incidents, and RCA data inherit project ownership.

## Production Docker / same-origin

When nginx proxies `/api/` to FastAPI, the SPA can use **relative** API URLs (`VITE_API_BASE_URL=""`) so HttpOnly cookies work on one origin. Set `BACKEND_CORS_ORIGINS` to the public SPA origin(s) even when proxying, for CSRF Origin checks on mutating requests.

## API hardening (Phase 7)

| Control | Implementation |
|---------|----------------|
| Production config validation | `validate_production_settings()` |
| CORS | `BACKEND_CORS_ORIGINS` — restrict in production |
| CSRF mitigation | Origin/Referer allowlist for cookie-auth mutating requests |
| Rate limiting | Auth + expensive endpoints (in-process) |
| Security headers | `SecurityHeadersMiddleware` in production |
| Upload limits | Size cap, extension allowlist, filename sanitization |
| Path traversal | `assert_path_within_storage()` |
| Error responses | Generic 500 body in production |

## Secrets

- Never commit `.env`.
- Generate JWT: `openssl rand -hex 32`.
- Replace placeholder `POSTGRES_PASSWORD` before any public deploy.

## Dependency audits

Run periodically:

```bash
cd backend && pip audit
cd frontend && npm audit
```

Document any accepted risks in this file when upgrades are deferred.

## Reporting

For a portfolio deployment, restrict network access until reviewed; rotate secrets if exposed.