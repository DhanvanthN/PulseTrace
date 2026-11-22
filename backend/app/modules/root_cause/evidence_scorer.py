from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.modules.root_cause.evidence_collector import TraceEvidence

CATEGORY_WEIGHTS = {
    "temporal": "rca_weight_temporal",
    "deployment": "rca_weight_deployment",
    "service": "rca_weight_service",
    "dependency": "rca_weight_dependency",
    "error_pattern": "rca_weight_error_pattern",
    "traffic": "rca_weight_traffic",
    "severity": "rca_weight_severity",
}


@dataclass
class ScoreResult:
    confidence_score: float
    supporting_evidence_count: int
    contradicting_evidence_count: int
    evidence_summary: dict


def score_candidate(evidence: list[TraceEvidence], settings: Settings) -> ScoreResult:
    """
    Deterministic 0–100 evidence strength (not calibrated probability).

    normalized = 100 * support / (support + contradict + epsilon)
    Each evidence_key is counted at most once per stance (no double-count).
    """
    support_keys: dict[str, float] = {}
    contradict_keys: dict[str, float] = {}

    for item in evidence:
        category = item.weight_category
        weight_key = CATEGORY_WEIGHTS.get(category, "rca_weight_temporal")
        magnitude = float(getattr(settings, weight_key, 10.0))
        if item.stance == "supporting":
            support_keys[item.evidence_key] = max(support_keys.get(item.evidence_key, 0.0), magnitude)
        else:
            contradict_keys[item.evidence_key] = max(
                contradict_keys.get(item.evidence_key, 0.0),
                settings.rca_contradiction_penalty,
            )

    support_total = sum(support_keys.values())
    contradict_total = sum(contradict_keys.values())
    confidence = 100.0 * support_total / (support_total + contradict_total + 0.01)
    confidence = round(min(100.0, max(0.0, confidence)), 2)

    items = [
        {
            "evidence_key": item.evidence_key,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
            "service_id": str(item.service_id) if item.service_id else None,
            "explanation": item.explanation,
            "stance": item.stance,
            "weight_category": item.weight_category,
        }
        for item in evidence
    ]

    return ScoreResult(
        confidence_score=confidence,
        supporting_evidence_count=len(support_keys),
        contradicting_evidence_count=len(contradict_keys),
        evidence_summary={
            "items": items,
            "score_breakdown": {
                "support_points": round(support_total, 3),
                "contradiction_points": round(contradict_total, 3),
                "formula": "100 * support / (support + contradict + 0.01)",
            },
            "score_note": (
                "Confidence score reflects relative evidence strength (0–100), not a statistical probability."
            ),
        },
    )