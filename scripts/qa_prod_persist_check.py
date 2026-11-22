#!/usr/bin/env python3
"""HTTP persistence checks against isolated QA stack (nginx on 8081)."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
STATE = Path(__file__).resolve().parents[1] / "deploy" / "qa-persist-state.json"


def post_json(path: str, data: dict, headers: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        json.dumps(data).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_json(path: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers=headers or {}, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> int:
    email = f"persist-{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass1!"
    post_json("/api/v1/auth/register", {"full_name": "Persist QA", "email": email, "password": password})
    token = post_json("/api/v1/auth/login", {"email": email, "password": password})["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    project = post_json("/api/v1/projects", {"name": "Persist", "environment": "staging"}, auth)
    pid = project["id"]

    line = b'{"timestamp":"2026-01-01T00:00:00Z","level":"ERROR","message":"persist test"}\n'
    boundary = "----pulsetracebound"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="p.jsonl"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + line + f"\r\n--{boundary}--\r\n".encode()
    upload_req = urllib.request.Request(
        f"{BASE}/api/v1/projects/{pid}/logs/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(upload_req) as resp:
        upload = json.loads(resp.read())

    logs = get_json(f"/api/v1/projects/{pid}/logs?limit=5", auth)
    log_id = logs["items"][0]["id"] if logs.get("items") else None

    STATE.write_text(
        json.dumps({"email": email, "project_id": pid, "batch_id": upload.get("id"), "log_id": log_id}),
        encoding="utf-8",
    )
    print("persist_seed_ok", pid, log_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())