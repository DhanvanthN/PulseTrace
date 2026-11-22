# Security Audit (defensive, local)

**Scope:** Application code review + automated ownership tests. Not a third-party penetration test.

## Controls in place

| Area | Implementation | Test / evidence |
|------|----------------|-----------------|
| Password storage | Argon2 | `test_auth.py` |
| API auth | JWT + optional HttpOnly cookie | Bearer + cookie paths |
| Project isolation | `get_owned_project` | `test_projects.py`, `test_security_isolation.py`, `test_analysis_project_isolation` |
| Upload validation | Extension allowlist, size cap, sanitize filename | `test_logs.py` |
| Path traversal helper | `resolve_stored_upload_path` | `test_resolve_stored_upload_path_rejects_traversal` |
| CSRF (cookie auth) | Origin/Referer middleware | Manual; skipped in `APP_ENV=test` |
| Rate limiting | In-memory per IP/path | Single-instance only |
| Production startup | JWT length/placeholder checks | `test_production.py` |
| Error sanitization | Generic 500 in production | `production.py` |
| Deployment diff sanitization | Strips secret-like keys | `test_sanitize_configuration_diff_strips_secrets` |

## Findings

| Severity | Finding | Mitigation |
|----------|---------|------------|
| **Low** | In-memory rate limiter not multi-instance safe | Document; use edge limits in real deploy |
| **Low** | JWT not revocable server-side | Short TTL; document |
| **Low** | No public file download endpoint; upload paths server-generated | `resolve_stored_upload_path` for future reads |
| **Medium** | npm moderate advisories in dev toolchain (esbuild/vitest) | Track upgrades; dev-only impact |
| **Info** | SQLAlchemy ORM — parameterized queries by default | No raw SQL string concat found in app routes |

## Not performed

- OWASP ZAP / DAST scan
- Dependency `pip audit` (unavailable in current venv)
- TLS/HSTS verification (no deploy)

## Safe testing only

All tests use local TestClient/Playwright against developer-controlled instances. No external attack traffic.