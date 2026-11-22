from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.modules.anomaly_detection.features import BucketFeatures
from app.modules.anomaly_detection.statistical import DetectedAnomaly
from app.modules.analysis.severity import classify_severity

FEATURE_COLUMNS = [
    "total_count",
    "error_count",
    "critical_count",
    "warning_count",
    "error_ratio",
    "critical_ratio",
    "unique_fingerprints",
    "request_count",
]


def detect_isolation_forest_anomalies(
    buckets: list[BucketFeatures],
    *,
    contamination: float,
    min_rows: int,
    random_state: int,
) -> list[DetectedAnomaly]:
    if len(buckets) < min_rows:
        return []

    matrix = pd.DataFrame([bucket.as_dict() for bucket in buckets])
    features = matrix[FEATURE_COLUMNS].astype(float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = IsolationForest(
        contamination=min(max(contamination, 0.01), 0.25),
        random_state=random_state,
        n_estimators=200,
    )
    preds = model.fit_predict(scaled)
    scores = -model.score_samples(scaled)

    detected: list[DetectedAnomaly] = []
    for index, bucket in enumerate(buckets):
        if preds[index] != -1:
            continue
        measured = bucket.as_dict()
        score = float(scores[index])
        severity = classify_severity(
            anomaly_type="multivariate_pattern",
            if_score=min(score / 3.0, 1.0),
            error_count=bucket.error_count,
            critical_count=bucket.critical_count,
        )
        dedupe_key = hashlib.sha256(
            f"if|{bucket.service_id}|{bucket.bucket_start.isoformat()}".encode()
        ).hexdigest()
        detected.append(
            DetectedAnomaly(
                anomaly_type="multivariate_pattern",
                severity=severity,
                score=score,
                description="Isolation Forest flagged an unusual feature combination",
                detection_method="isolation_forest",
                start_time=bucket.bucket_start,
                end_time=bucket.bucket_end,
                service_id=bucket.service_id,
                evidence={
                    "time_window": {
                        "start": bucket.bucket_start.isoformat(),
                        "end": bucket.bucket_end.isoformat(),
                    },
                    "measured": measured,
                    "model": {
                        "algorithm": "IsolationForest",
                        "contamination": contamination,
                        "feature_columns": FEATURE_COLUMNS,
                        "scaled_contributions": {
                            col: round(float(scaled[index][col_idx]), 4)
                            for col_idx, col in enumerate(FEATURE_COLUMNS)
                        },
                    },
                    "rule": "prediction == outlier (-1)",
                    "score_note": "Score is an isolation-based anomaly score, not a probability.",
                },
                dedupe_key=dedupe_key,
            )
        )
    return detected