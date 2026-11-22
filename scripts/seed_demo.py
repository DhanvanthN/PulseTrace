#!/usr/bin/env python3
"""
Seed the ShopFlow demonstration dataset through the real log ingestion pipeline.

Usage (from repository root):
  python scripts/seed_demo.py --create-demo-user --password 'YourSecurePass1!'
  python scripts/seed_demo.py --email demo@shopflow-demo.pulsetrace --password '...'

Does not insert anomalies, incidents, or RCA rows directly — run analysis / correlate / investigate in the UI or API.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_local
from app.models.deployment import Deployment
from app.models.project import Project
from app.models.service import Service
from app.models.service_dependency import ServiceDependency
from app.models.user import User
from app.models.log_batch import LogBatch
from app.modules.logs.processor import process_log_batch
from app.modules.logs.storage import detect_format, resolve_storage_root, save_upload_stream
from app.repositories.log_batch_repository import LogBatchRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository

DEMO_EMAIL_DEFAULT = "demo@shopflow-demo.pulsetrace"
DEMO_FULL_NAME = "ShopFlow Demo User"
DEMO_PROJECT_NAME = "ShopFlow (Demonstration)"
DEMO_MARKER = "synthetic-shopflow-v1"
SERVICES = (
    ("API Gateway", "api", "Edge HTTP gateway for ShopFlow"),
    ("Authentication Service", "auth", "JWT issuance and session validation"),
    ("Payment Service", "api", "Checkout and payment capture"),
    ("Inventory Service", "api", "Stock reservations and catalog"),
    ("Database Service", "database", "Primary PostgreSQL cluster"),
)


def _ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_shopflow_jsonl(anchor: datetime) -> bytes:
    """Synthetic incident: DB degradation -> dependent services -> gateway errors; deploy near window."""
    lines: list[str] = []

    def emit(ts: datetime, service: str, level: str, message: str, request_id: str | None = None) -> None:
        payload = {"timestamp": _ts(ts), "level": level, "service": service, "message": message}
        if request_id:
            payload["request_id"] = request_id
        lines.append(json.dumps(payload))

    for hour in range(8, 1, -1):
        t = anchor - timedelta(hours=hour)
        for _ in range(12):
            emit(t, "API Gateway", "INFO", "request completed status=200 route=/health")
        for _ in range(6):
            emit(t, "Authentication Service", "INFO", "token validated subject=shopper")
        emit(t, "Payment Service", "INFO", "charge authorized amount_cents=2499")
        emit(t, "Inventory Service", "INFO", "stock reserved sku=SKU-4421 qty=1")
        emit(t, "Database Service", "INFO", "query ok pool_active=3")

    incident_start = anchor - timedelta(hours=2, minutes=45)
    for minute in range(0, 50, 5):
        t = incident_start + timedelta(minutes=minute)
        emit(t, "Database Service", "ERROR", "connection pool exhausted waiting=30s")
        emit(t, "Database Service", "WARNING", "slow query duration_ms=4200 table=orders")

    cascade_start = anchor - timedelta(hours=2, minutes=15)
    for i in range(0, 18):
        t = cascade_start + timedelta(minutes=i * 3)
        rid = f"req-shopflow-{i:04d}"
        emit(t, "Payment Service", "ERROR", "checkout failed upstream database timeout", rid)
        emit(t, "Inventory Service", "ERROR", "reservation failed database unavailable", rid)

    deploy_at = anchor - timedelta(hours=1, minutes=20)
    emit(deploy_at, "API Gateway", "INFO", "deploy completed version=2.4.1 change=rate-limit-tuning")

    gateway_spike = anchor - timedelta(minutes=35)
    for _ in range(8):
        emit(gateway_spike, "API Gateway", "ERROR", "upstream timeout service=payment-service duration_ms=30000")
    for _ in range(5):
        emit(gateway_spike, "API Gateway", "ERROR", "502 bad gateway dependency=inventory-service")

    pre_deploy_noise = deploy_at - timedelta(minutes=25)
    emit(pre_deploy_noise, "API Gateway", "ERROR", "baseline latency spike route=/checkout p95_ms=890")

    latest = anchor - timedelta(minutes=5)
    for _ in range(4):
        emit(latest, "API Gateway", "CRITICAL", "circuit open downstream database-service failures=12")
    emit(latest, "Database Service", "CRITICAL", "primary replica lag_seconds=180 replication halted")

    return ("\n".join(lines) + "\n").encode("utf-8")


async def _save_bytes_to_upload(
    db,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content: bytes,
) -> Path:
    batch_repo = LogBatchRepository(db)
    batch = batch_repo.create(
        project_id=project_id,
        uploaded_by=user_id,
        filename=filename,
        file_format=detect_format(filename),
        storage_path="",
    )
    db.flush()

    from io import BytesIO
    from starlette.datastructures import UploadFile, Headers

    upload = UploadFile(filename=filename, file=BytesIO(content), headers=Headers({}))
    file_path, file_format, _size = await save_upload_stream(
        upload,
        project_id=project_id,
        batch_id=batch.id,
    )
    batch.file_format = file_format
    batch.storage_path = str(file_path.relative_to(resolve_storage_root()).as_posix())
    db.flush()
    process_log_batch(db, batch=batch, file_path=file_path, forced_service_id=None)
    db.commit()
    db.refresh(batch)
    return file_path


def save_bytes_sync(db, **kwargs) -> None:
    import asyncio

    asyncio.run(_save_bytes_to_upload(db, **kwargs))


def ensure_demo_user(db, email: str, password: str, create: bool) -> User:
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user:
        return user
    if not create:
        raise SystemExit(
            f"No user {email}. Re-run with --create-demo-user to register the demonstration account."
        )
    user = repo.create(
        email=email,
        full_name=DEMO_FULL_NAME,
        password_hash=hash_password(password),
    )
    db.commit()
    db.refresh(user)
    print(f"Created demonstration user: {email}")
    return user


def ensure_project(db, owner_id: uuid.UUID) -> Project:
    existing = db.scalars(
        select(Project).where(Project.owner_id == owner_id, Project.name == DEMO_PROJECT_NAME)
    ).first()
    if existing:
        print(f"Using existing project: {existing.name} ({existing.id})")
        return existing
    project = ProjectRepository(db).create(
        owner_id=owner_id,
        name=DEMO_PROJECT_NAME,
        description=(
            "Synthetic ShopFlow e-commerce stack for portfolio demos. "
            f"Marker: {DEMO_MARKER}. Not production data."
        ),
        environment="staging",
    )
    db.commit()
    db.refresh(project)
    print(f"Created project: {project.name} ({project.id})")
    return project


def ensure_services(db, project_id: uuid.UUID) -> dict[str, Service]:
    repo = ServiceRepository(db)
    by_name: dict[str, Service] = {}
    for name, service_type, description in SERVICES:
        existing = db.scalars(
            select(Service).where(Service.project_id == project_id, Service.name == name)
        ).first()
        if existing:
            by_name[name] = existing
            continue
        row = Service(
            project_id=project_id,
            name=name,
            service_type=service_type,
            environment="staging",
            description=description,
        )
        db.add(row)
        db.flush()
        by_name[name] = row
    db.commit()
    return by_name


def ensure_dependencies(db, services: dict[str, Service]) -> None:
    pairs = (
        ("API Gateway", "Authentication Service"),
        ("API Gateway", "Payment Service"),
        ("API Gateway", "Inventory Service"),
        ("Payment Service", "Database Service"),
        ("Inventory Service", "Database Service"),
        ("Authentication Service", "Database Service"),
    )
    for upstream_name, downstream_name in pairs:
        upstream = services[upstream_name]
        downstream = services[downstream_name]
        exists = db.scalars(
            select(ServiceDependency).where(
                ServiceDependency.upstream_service_id == upstream.id,
                ServiceDependency.downstream_service_id == downstream.id,
            )
        ).first()
        if exists:
            continue
        db.add(
            ServiceDependency(
                upstream_service_id=upstream.id,
                downstream_service_id=downstream.id,
            )
        )
    db.commit()


def ensure_deployment(db, project_id: uuid.UUID, gateway: Service, deployed_at: datetime) -> None:
    version = "2.4.1"
    exists = db.scalars(
        select(Deployment).where(
            Deployment.project_id == project_id,
            Deployment.version == version,
            Deployment.service_id == gateway.id,
        )
    ).first()
    if exists:
        return
    db.add(
        Deployment(
            project_id=project_id,
            service_id=gateway.id,
            version=version,
            change_type="release",
            description="Demonstration deployment: rate-limit tuning (synthetic)",
            configuration_diff={"rate_limit_rpm": {"from": 1200, "to": 800}},
            deployed_at=deployed_at,
        )
    )
    db.commit()


def logs_already_seeded(db, project_id: uuid.UUID) -> bool:
    return (
        db.scalars(
            select(LogBatch).where(
                LogBatch.project_id == project_id,
                LogBatch.filename == "shopflow_incident.jsonl",
            )
        ).first()
        is not None
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ShopFlow demonstration data")
    parser.add_argument("--email", default=DEMO_EMAIL_DEFAULT)
    parser.add_argument("--password", default=None, help="Required when --create-demo-user is set")
    parser.add_argument("--create-demo-user", action="store_true")
    parser.add_argument("--force-reingest", action="store_true", help="Upload logs even if batch exists")
    args = parser.parse_args()

    if args.create_demo_user and not args.password:
        raise SystemExit("--password is required with --create-demo-user")

    session_factory = get_session_local()
    db = session_factory()
    try:
        user = ensure_demo_user(db, args.email, args.password or "", args.create_demo_user)
        project = ensure_project(db, user.id)
        services = ensure_services(db, project.id)
        ensure_dependencies(db, services)

        anchor = datetime.now(timezone.utc)
        deploy_at = anchor - timedelta(hours=1, minutes=20)
        ensure_deployment(db, project.id, services["API Gateway"], deploy_at)

        if logs_already_seeded(db, project.id) and not args.force_reingest:
            print("Log batch shopflow_incident.jsonl already exists; skip upload (use --force-reingest).")
        else:
            content = build_shopflow_jsonl(anchor)
            save_bytes_sync(
                db,
                project_id=project.id,
                user_id=user.id,
                filename="shopflow_incident.jsonl",
                content=content,
            )
            print("Imported shopflow_incident.jsonl via ingestion pipeline.")

        print("\nNext steps (API or UI):")
        print(f"  1. Sign in as {args.email}")
        print(f"  2. Open project '{DEMO_PROJECT_NAME}'")
        print("  3. POST .../analysis/run")
        print("  4. POST .../incidents/correlate")
        print("  5. POST .../incidents/{id}/investigate")
    finally:
        db.close()


if __name__ == "__main__":
    main()