from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import pandas as pd

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass
class BucketFeatures:
    bucket_start: datetime
    bucket_end: datetime
    service_id: UUID | None
    total_count: int
    error_count: int
    critical_count: int
    warning_count: int
    unique_fingerprints: int
    request_count: int

    @property
    def error_ratio(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.error_count / self.total_count

    @property
    def critical_ratio(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.critical_count / self.total_count

    def as_dict(self) -> dict:
        return {
            "total_count": self.total_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "error_ratio": round(self.error_ratio, 4),
            "critical_ratio": round(self.critical_ratio, 4),
            "unique_fingerprints": self.unique_fingerprints,
            "request_count": self.request_count,
        }


def logs_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "level",
                "service_id",
                "fingerprint",
                "request_id",
                "log_id",
                "message",
            ]
        )
    return pd.DataFrame(rows)


def build_hourly_buckets(df: pd.DataFrame, bucket_minutes: int) -> list[BucketFeatures]:
    if df.empty:
        return []

    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["bucket"] = frame["timestamp"].dt.floor(f"{bucket_minutes}min")
    grouped = frame.groupby(["bucket", "service_id"], dropna=False)

    buckets: list[BucketFeatures] = []
    for (bucket_start, service_id), group in grouped:
        bucket_end = bucket_start + pd.Timedelta(minutes=bucket_minutes)
        level_counts = group["level"].str.upper().value_counts()
        buckets.append(
            BucketFeatures(
                bucket_start=bucket_start.to_pydatetime(),
                bucket_end=bucket_end.to_pydatetime(),
                service_id=service_id if pd.notna(service_id) else None,
                total_count=int(len(group)),
                error_count=int(level_counts.get("ERROR", 0)),
                critical_count=int(level_counts.get("CRITICAL", 0)),
                warning_count=int(level_counts.get("WARNING", 0)),
                unique_fingerprints=int(group["fingerprint"].nunique()),
                request_count=int(group["request_id"].notna().sum()),
            )
        )
    buckets.sort(key=lambda item: item.bucket_start)
    return buckets


def bucket_features_matrix(buckets: list[BucketFeatures]) -> pd.DataFrame:
    if not buckets:
        return pd.DataFrame()
    return pd.DataFrame([bucket.as_dict() for bucket in buckets])