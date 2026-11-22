from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from app.modules.anomaly_detection.features import BucketFeatures
from app.modules.analysis.severity import classify_severity


@dataclass
class DetectedAnomaly:
    anomaly_type: str
    severity: str
    score: float
    description: str
    detection_method: str
    start_time: object
    end_time: object
    service_id: object
    evidence: dict
    dedupe_key: str


def _dedupe_key(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _z_score(value: float, mean: float, std: float) -> float | None:
    if std <= 1e-9:
        return None
    return (value - mean) / std


def detect_statistical_anomalies(
    buckets: list[BucketFeatures],
    *,
    min_samples: int,
    z_threshold: float,
) -> list[DetectedAnomaly]:
    if len(buckets) < min_samples + 1:
        return []

    history = buckets[:-1]
    latest = buckets[-1]
    if latest.total_count == 0:
        return []

    history_totals = np.array([b.total_count for b in history], dtype=float)
    history_errors = np.array([b.error_count for b in history], dtype=float)
    history_critical = np.array([b.critical_count for b in history], dtype=float)

    if len(history_totals) < min_samples:
        return []

    detected: list[DetectedAnomaly] = []

    checks = [
        ("log_volume_spike", latest.total_count, float(np.mean(history_totals)), float(np.std(history_totals))),
        ("error_spike", latest.error_count, float(np.mean(history_errors)), float(np.std(history_errors))),
        ("critical_spike", latest.critical_count, float(np.mean(history_critical)), float(np.std(history_critical))),
    ]

    for anomaly_type, observed, mean, std in checks:
        if observed <= 0:
            continue
        z = _z_score(observed, mean, std)
        if z is None or z < z_threshold:
            continue
        if observed < min_samples and anomaly_type == "log_volume_spike":
            continue

        severity = classify_severity(
            anomaly_type=anomaly_type,
            z_score=z,
            critical_count=latest.critical_count,
            error_count=latest.error_count,
        )
        evidence = {
            "time_window": {
                "start": latest.bucket_start.isoformat(),
                "end": latest.bucket_end.isoformat(),
            },
            "measured": latest.as_dict(),
            "baseline": {
                "mean_total": round(mean, 3),
                "std_total": round(std, 3),
            },
            "rule": f"z_score >= {z_threshold}",
            "z_score": round(float(z), 4),
            "score_note": "Anomaly score is a standardized deviation, not a probability.",
        }
        detected.append(
            DetectedAnomaly(
                anomaly_type=anomaly_type,
                severity=severity,
                score=float(z),
                description=f"Statistical {anomaly_type.replace('_', ' ')} detected in latest window",
                detection_method="statistical_zscore",
                start_time=latest.bucket_start,
                end_time=latest.bucket_end,
                service_id=latest.service_id,
                evidence=evidence,
                dedupe_key=_dedupe_key(
                    [
                        "statistical",
                        anomaly_type,
                        str(latest.service_id),
                        latest.bucket_start.isoformat(),
                    ]
                ),
            )
        )

    history_error_ratio = np.array([b.error_ratio for b in history], dtype=float)
    if latest.total_count >= min_samples and len(history_error_ratio) >= min_samples:
        mean_ratio = float(np.mean(history_error_ratio))
        std_ratio = float(np.std(history_error_ratio))
        z_ratio = _z_score(latest.error_ratio, mean_ratio, std_ratio)
        if z_ratio is not None and z_ratio >= z_threshold and latest.error_count > 0:
            severity = classify_severity(
                anomaly_type="error_ratio",
                z_score=z_ratio,
                error_count=latest.error_count,
            )
            evidence = {
                "time_window": {
                    "start": latest.bucket_start.isoformat(),
                    "end": latest.bucket_end.isoformat(),
                },
                "measured": {"error_ratio": round(latest.error_ratio, 4), **latest.as_dict()},
                "baseline": {"mean_error_ratio": round(mean_ratio, 4), "std_error_ratio": round(std_ratio, 4)},
                "rule": f"error_ratio z_score >= {z_threshold}",
                "z_score": round(float(z_ratio), 4),
            }
            detected.append(
                DetectedAnomaly(
                    anomaly_type="error_ratio_spike",
                    severity=severity,
                    score=float(z_ratio),
                    description="Abnormal error-to-total log ratio in latest window",
                    detection_method="statistical_zscore",
                    start_time=latest.bucket_start,
                    end_time=latest.bucket_end,
                    service_id=latest.service_id,
                    evidence=evidence,
                    dedupe_key=_dedupe_key(
                        ["statistical", "error_ratio", str(latest.service_id), latest.bucket_start.isoformat()]
                    ),
                )
            )

    return detected