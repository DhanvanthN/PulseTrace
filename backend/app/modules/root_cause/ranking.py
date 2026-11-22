from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RankedDraft:
    cause_type: str
    title: str
    explanation: str
    candidate_key: str
    service_id: object
    deployment_id: object
    confidence_score: float
    supporting_evidence_count: int
    contradicting_evidence_count: int
    evidence_summary: dict
    ranking: int = 0


def rank_drafts(drafts: list[RankedDraft]) -> list[RankedDraft]:
    ordered = sorted(
        drafts,
        key=lambda item: (-item.confidence_score, item.cause_type, item.title),
    )
    for index, item in enumerate(ordered, start=1):
        item.ranking = index
    return ordered