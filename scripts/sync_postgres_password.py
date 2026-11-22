"""Align the pulsetrace DB role password with POSTGRES_PASSWORD in the root .env (no volume reset)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def load_postgres_password(env_path: Path) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^POSTGRES_PASSWORD=(.*)$", line.strip())
        if match:
            return match.group(1)
    raise RuntimeError("POSTGRES_PASSWORD not found in .env")


def dollar_quote(value: str) -> str:
    tag = "pt_pw"
    while f"${tag}$" in value:
        tag += "x"
    return f"${tag}${value}${tag}$"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"
    password = load_postgres_password(env_path)

    docker = (
        Path.home()
        / "AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
    )
    if not docker.is_file():
        docker = Path("docker")

    container = "pulsetrace-postgres"
    sql = f"ALTER USER pulsetrace WITH PASSWORD {dollar_quote(password)};"

    completed = subprocess.run(
        [
            str(docker),
            "exec",
            container,
            "psql",
            "-U",
            "pulsetrace",
            "-d",
            "pulsetrace",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "unknown error").strip()
        print("Failed to update database role password.", file=sys.stderr)
        print(message[:500], file=sys.stderr)
        return completed.returncode

    print("Database role password synchronized with .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())