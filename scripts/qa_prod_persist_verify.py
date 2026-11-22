#!/usr/bin/env python3
"""Verify persisted QA data still readable after container restart."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081"
STATE = Path(__file__).resolve().parents[1] / "deploy" / "qa-persist-state.json"


def post_json(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_json(path: str, headers: dict) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    token = post_json("/api/v1/auth/login", {"email": state["email"], "password": "SecurePass1!"})[
        "access_token"
    ]
    auth = {"Authorization": f"Bearer {token}"}
    pid = state["project_id"]
    logs = get_json(f"/api/v1/projects/{pid}/logs?limit=5", auth)
    assert logs["total"] >= 1, "logs missing after restart"
    if state.get("log_id"):
        detail = get_json(f"/api/v1/projects/{pid}/logs/{state['log_id']}", auth)
        assert "persist test" in detail.get("message", ""), "log detail mismatch"
    print("persist_verify_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())