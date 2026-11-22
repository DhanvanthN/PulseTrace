from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Iterator

VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
LEVEL_ALIASES = {
    "WARN": "WARNING",
    "ERR": "ERROR",
    "FATAL": "CRITICAL",
    "TRACE": "DEBUG",
}

TIMESTAMP_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
)

STRUCTURED_TXT = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    r"\s+(?P<level>[A-Za-z]+)\s+(?P<msg>.+)$"
)

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "timestamp": ("timestamp", "time", "datetime", "ts", "@timestamp"),
    "level": ("level", "severity", "loglevel", "log_level"),
    "service": ("service", "service_name", "service.name", "app"),
    "message": ("message", "msg", "log", "text"),
    "trace_id": ("trace_id", "traceid", "trace"),
    "request_id": ("request_id", "requestid", "req_id"),
}


@dataclass
class NormalizedLogRecord:
    timestamp: datetime
    level: str
    message: str
    service_name: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parse_error: str | None = None


@dataclass
class ParseOutcome:
    record: NormalizedLogRecord | None
    error: str | None = None


def normalize_level(value: str | None, *, default: str = "INFO") -> str:
    if not value:
        return default
    upper = value.strip().upper()
    upper = LEVEL_ALIASES.get(upper, upper)
    if upper not in VALID_LEVELS:
        return default
    return upper


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in TIMESTAMP_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _pick_field(raw: dict[str, Any], field_name: str) -> Any:
    aliases = COLUMN_ALIASES[field_name]
    lowered = {str(k).lower(): v for k, v in raw.items()}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def normalize_mapping(
    raw: dict[str, Any],
    *,
    default_service: str | None = None,
    fallback_ts: datetime | None = None,
) -> ParseOutcome:
    ts = parse_timestamp(_pick_field(raw, "timestamp")) or fallback_ts
    if ts is None:
        return ParseOutcome(record=None, error="Missing or unparseable timestamp")

    level = normalize_level(_pick_field(raw, "level"))
    message_val = _pick_field(raw, "message")
    if message_val is None:
        return ParseOutcome(record=None, error="Missing message field")
    message = str(message_val).strip()
    if not message:
        return ParseOutcome(record=None, error="Empty message")

    service_name = _pick_field(raw, "service")
    if service_name is None and default_service:
        service_name = default_service
    service_name = str(service_name).strip() if service_name else None

    trace_id = _pick_field(raw, "trace_id")
    request_id = _pick_field(raw, "request_id")

    metadata = {
        k: v
        for k, v in raw.items()
        if str(k).lower()
        not in {
            "timestamp",
            "time",
            "datetime",
            "ts",
            "level",
            "severity",
            "message",
            "msg",
            "service",
            "service_name",
            "trace_id",
            "request_id",
        }
    }
    if service_name and not _pick_field(raw, "service"):
        metadata.setdefault("original_service_name", service_name)

    return ParseOutcome(
        record=NormalizedLogRecord(
            timestamp=ts,
            level=level,
            message=message,
            service_name=service_name,
            trace_id=str(trace_id).strip() if trace_id else None,
            request_id=str(request_id).strip() if request_id else None,
            metadata=metadata,
        )
    )


def iter_jsonl_records(lines: Iterator[str]) -> Iterator[ParseOutcome]:
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError as exc:
            yield ParseOutcome(record=None, error=f"line {line_no}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(raw, dict):
            yield ParseOutcome(record=None, error=f"line {line_no}: expected JSON object")
            continue
        outcome = normalize_mapping(raw)
        if outcome.error:
            yield ParseOutcome(record=None, error=f"line {line_no}: {outcome.error}")
        else:
            yield outcome


def iter_json_records(text: str) -> Iterator[ParseOutcome]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        yield ParseOutcome(record=None, error=f"Invalid JSON document: {exc.msg}")
        return

    items: list[Any]
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        if "logs" in payload and isinstance(payload["logs"], list):
            items = payload["logs"]
        else:
            items = [payload]
    else:
        yield ParseOutcome(record=None, error="JSON root must be object or array")
        return

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            yield ParseOutcome(record=None, error=f"entry {index}: expected object")
            continue
        outcome = normalize_mapping(item)
        if outcome.error:
            yield ParseOutcome(record=None, error=f"entry {index}: {outcome.error}")
        else:
            yield outcome


def iter_csv_records(text: str) -> Iterator[ParseOutcome]:
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        yield ParseOutcome(record=None, error="CSV header row missing")
        return
    for row_no, row in enumerate(reader, start=2):
        outcome = normalize_mapping(row)
        if outcome.error:
            yield ParseOutcome(record=None, error=f"row {row_no}: {outcome.error}")
        else:
            yield outcome


def iter_txt_records(lines: Iterator[str]) -> Iterator[ParseOutcome]:
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        match = STRUCTURED_TXT.match(stripped)
        if match:
            ts = parse_timestamp(match.group("ts"))
            if ts is None:
                yield ParseOutcome(record=None, error=f"line {line_no}: unparseable timestamp")
                continue
            yield ParseOutcome(
                record=NormalizedLogRecord(
                    timestamp=ts,
                    level=normalize_level(match.group("level")),
                    message=match.group("msg").strip(),
                    metadata={"source_format": "txt_structured"},
                )
            )
            continue
        yield ParseOutcome(
            record=NormalizedLogRecord(
                timestamp=datetime.now(timezone.utc),
                level="INFO",
                message=stripped,
                metadata={"source_format": "txt_unstructured"},
            )
        )