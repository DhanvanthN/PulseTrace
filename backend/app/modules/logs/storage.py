from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_EXTENSIONS = frozenset({".csv", ".json", ".jsonl", ".txt"})
EXTENSION_TO_FORMAT = {
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".txt": "txt",
}


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if base in {"", ".", ".."}:
        base = "upload.log"
    return base[:200]


def detect_format(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return EXTENSION_TO_FORMAT[suffix]


def resolve_storage_root() -> Path:
    settings = get_settings()
    root = Path(settings.log_storage_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_stored_upload_path(relative_path: str) -> Path:
    """Resolve a batch-relative storage path to an absolute path under the storage root."""
    storage_root = resolve_storage_root()
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in Path(normalized).parts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")
    candidate = (storage_root / normalized).resolve()
    return assert_path_within_storage(candidate, storage_root)


def assert_path_within_storage(path: Path, root: Path | None = None) -> Path:
    """Prevent path traversal when resolving stored upload paths."""
    storage_root = root or resolve_storage_root()
    resolved = path.resolve()
    if not str(resolved).startswith(str(storage_root)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage path",
        )
    return resolved


async def save_upload_stream(
    upload: UploadFile,
    *,
    project_id: uuid.UUID,
    batch_id: uuid.UUID,
) -> tuple[Path, str, int]:
    settings = get_settings()
    original_name = sanitize_filename(upload.filename or "upload.log")
    file_format = detect_format(original_name)

    relative_dir = Path(str(project_id)) / str(batch_id)
    storage_root = resolve_storage_root()
    target_dir = storage_root / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    storage_name = f"{uuid.uuid4().hex}_{original_name}"
    target_path = target_dir / storage_name

    total_bytes = 0
    chunk_size = 1024 * 1024
    try:
        with target_path.open("wb") as out_file:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.log_upload_max_bytes:
                    out_file.close()
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds limit of {settings.log_upload_max_bytes} bytes",
                    )
                out_file.write(chunk)
    finally:
        await upload.close()

    if total_bytes == 0:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    storage_path = str(relative_dir / storage_name).replace("\\", "/")
    return target_path, file_format, total_bytes