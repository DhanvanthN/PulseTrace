import hashlib
import json


def build_fingerprint(
    *,
    level: str,
    message: str,
    service_name: str | None,
    trace_id: str | None,
) -> str:
    payload = {
        "level": level.upper(),
        "message": message.strip(),
        "service": (service_name or "").strip().lower(),
        "trace_id": (trace_id or "").strip(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()