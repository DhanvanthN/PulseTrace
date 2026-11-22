from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.log import Log
from app.models.log_batch import LogBatch
from app.modules.logs.fingerprint import build_fingerprint
from app.modules.logs.normalizer import (
    NormalizedLogRecord,
    ParseOutcome,
    iter_csv_records,
    iter_json_records,
    iter_jsonl_records,
    iter_txt_records,
)
from app.repositories.service_repository import ServiceRepository

logger = logging.getLogger(__name__)


def _append_error(errors: list[str], message: str) -> None:
    settings = get_settings()
    errors.append(message)
    while len("\n".join(errors)) > settings.log_error_summary_max_chars and errors:
        errors.pop(0)


def _iter_records(file_path: Path, file_format: str) -> Iterator[ParseOutcome]:
    if file_format == "jsonl":

        def line_iter() -> Iterator[str]:
            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    yield line

        yield from iter_jsonl_records(line_iter())
        return

    if file_format == "txt":

        def line_iter() -> Iterator[str]:
            with file_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    yield line

        yield from iter_txt_records(line_iter())
        return

    text = file_path.read_text(encoding="utf-8", errors="replace")
    if file_format == "csv":
        yield from iter_csv_records(text)
    elif file_format == "json":
        yield from iter_json_records(text)
    else:
        yield ParseOutcome(record=None, error=f"Unsupported parser for format '{file_format}'")


def _resolve_service_id(
    service_map: dict[str, uuid.UUID],
    record: NormalizedLogRecord,
    forced_service_id: uuid.UUID | None,
) -> tuple[uuid.UUID | None, dict]:
    metadata = dict(record.metadata)
    if forced_service_id is not None:
        return forced_service_id, metadata

    if not record.service_name:
        return None, metadata

    service_id = service_map.get(record.service_name.strip().lower())
    if service_id is None:
        metadata.setdefault("original_service_name", record.service_name)
    return service_id, metadata


def process_log_batch(
    db: Session,
    *,
    batch: LogBatch,
    file_path: Path,
    forced_service_id: uuid.UUID | None = None,
) -> LogBatch:
    settings = get_settings()
    batch.status = "processing"
    db.flush()

    service_map = ServiceRepository(db).name_map_for_project(batch.project_id)
    errors: list[str] = []
    buffer: list[Log] = []

    total = 0
    processed = 0
    failed = 0

    try:
        for outcome in _iter_records(file_path, batch.file_format):
            total += 1
            if outcome.error or outcome.record is None:
                failed += 1
                _append_error(errors, outcome.error or "Unknown parse error")
                continue

            record = outcome.record
            service_id, metadata = _resolve_service_id(service_map, record, forced_service_id)
            fingerprint = build_fingerprint(
                level=record.level,
                message=record.message,
                service_name=record.service_name,
                trace_id=record.trace_id,
            )

            buffer.append(
                Log(
                    project_id=batch.project_id,
                    batch_id=batch.id,
                    service_id=service_id,
                    timestamp=record.timestamp,
                    level=record.level,
                    message=record.message,
                    trace_id=record.trace_id,
                    request_id=record.request_id,
                    log_metadata=metadata,
                    fingerprint=fingerprint,
                )
            )
            processed += 1

            if len(buffer) >= settings.log_insert_batch_size:
                db.add_all(buffer)
                db.flush()
                buffer.clear()

        if buffer:
            db.add_all(buffer)
            db.flush()

        batch.total_records = total
        batch.processed_records = processed
        batch.failed_records = failed
        batch.error_summary = "\n".join(errors) if errors else None
        batch.completed_at = datetime.now(timezone.utc)

        if total == 0:
            batch.status = "failed"
            batch.error_summary = "No parseable records found in file"
        elif failed == 0 and processed > 0:
            batch.status = "completed"
        elif processed > 0:
            batch.status = "partially_completed"
        else:
            batch.status = "failed"

        db.flush()
        logger.info(
            "Processed log batch batch_id=%s total=%s processed=%s failed=%s status=%s",
            batch.id,
            total,
            processed,
            failed,
            batch.status,
        )
        return batch
    except Exception:
        logger.exception("Log batch processing failed batch_id=%s", batch.id)
        batch.status = "failed"
        batch.completed_at = datetime.now(timezone.utc)
        _append_error(errors, "Internal processing error")
        batch.error_summary = "\n".join(errors)
        db.flush()
        raise