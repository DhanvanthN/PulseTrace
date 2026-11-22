# Database and Upload Backup / Recovery

## PostgreSQL backup (logical)

From the host (adjust port **5433** if that is your `POSTGRES_PORT`):

```powershell
$env:PGPASSWORD = "your_password"
pg_dump -h localhost -p 5433 -U pulsetrace -d pulsetrace -Fc -f pulsetrace_backup.dump
```

Plain SQL:

```bash
pg_dump -h localhost -p 5433 -U pulsetrace pulsetrace > pulsetrace.sql
```

Docker exec (container name `pulsetrace-postgres`):

```bash
docker exec pulsetrace-postgres pg_dump -U pulsetrace pulsetrace -Fc > pulsetrace_backup.dump
```

## Restore (destructive — new database only)

**Do not** restore over production without explicit approval and a maintenance window.

```powershell
$env:PGPASSWORD = "your_password"
createdb -h localhost -p 5433 -U pulsetrace pulsetrace_restored
pg_restore -h localhost -p 5433 -U pulsetrace -d pulsetrace_restored --no-owner pulsetrace_backup.dump
```

Update `DATABASE_URL` to point at the restored database, then:

```bash
cd backend && alembic current
```

Head should be `d7e8f9a0b1c2`.

## Migrations

```bash
cd backend
alembic upgrade head
alembic current
alembic history
```

## Uploaded log files

Files live under `LOG_STORAGE_PATH` (default `data/uploads/` relative to repo). Back up the directory tree:

```powershell
Compress-Archive -Path .\data\uploads -DestinationPath uploads_backup.zip
```

In `docker-compose.prod.yml`, the named volume `pulsetrace_uploads` maps to `/app/data/uploads` in the backend container.

**Isolated QA stack** (`docker-compose.prod.qa.yml`, project `pulsetrace-prod-qa`): volumes `pulsetrace-prod-qa_pgdata_qa` and `pulsetrace-prod-qa_uploads_qa` — separate from development data. Back up QA volumes only when you intentionally keep that environment.

## Recovery considerations

- Restoring DB without upload files leaves `LogBatch.storage_path` rows pointing at missing files; re-upload or restore disk snapshot.
- JWT tokens remain valid until expiry after DB restore (no server-side revocation list).
- Run smoke tests: login, list logs, open incident report.

## Scripts

`scripts/backup_postgres.ps1` — example wrapper for Windows (edit credentials locally; do not commit secrets).