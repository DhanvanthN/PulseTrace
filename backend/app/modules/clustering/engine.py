from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

from app.modules.clustering.text_normalize import normalize_message_for_clustering


@dataclass
class ClusterResult:
    cluster_label: str
    description: str
    representative_message: str
    log_ids: list
    log_count: int
    first_seen: datetime | None
    last_seen: datetime | None


def cluster_log_messages(
    records: list[dict],
    *,
    eps: float,
    min_samples: int,
    max_clusters: int,
) -> tuple[list[ClusterResult], int]:
    if not records:
        return [], 0

    normalized = [normalize_message_for_clustering(record["message"]) for record in records]
    vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(normalized)

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine", n_jobs=1)
    labels = clustering.fit_predict(matrix)

    noise_count = int(np.sum(labels == -1))
    clusters: list[ClusterResult] = []

    unique_labels = sorted({int(label) for label in labels if label != -1})
    for label in unique_labels[:max_clusters]:
        indices = [idx for idx, value in enumerate(labels) if value == label]
        selected = [records[idx] for idx in indices]
        representative = min(selected, key=lambda item: len(item["message"]))["message"]
        timestamps = [item["timestamp"] for item in selected]
        clusters.append(
            ClusterResult(
                cluster_label=f"C{label:03d}",
                description="Text-similarity cluster (TF-IDF + DBSCAN); not semantic understanding.",
                representative_message=representative,
                log_ids=[item["log_id"] for item in selected],
                log_count=len(selected),
                first_seen=min(timestamps),
                last_seen=max(timestamps),
            )
        )

    clusters.sort(key=lambda item: item.log_count, reverse=True)
    return clusters, noise_count