from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rca import RCAInvestigation, RootCauseCandidate
from app.modules.root_cause.candidate_generator import generate_candidates
from app.modules.root_cause.evidence_collector import collect_investigation_context
from app.modules.root_cause.evidence_scorer import score_candidate
from app.modules.root_cause.explanations import build_candidate_explanation, build_investigation_summary
from app.modules.root_cause.ranking import RankedDraft, rank_drafts

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_rca_investigation(db: Session, *, project_id: UUID, incident_id: UUID) -> dict:
    settings = get_settings()
    ctx = collect_investigation_context(db, project_id=project_id, incident_id=incident_id)
    if ctx is None:
        return {"status": "not_found", "message": "Incident not found"}

    next_version = (
        db.scalar(
            select(func.max(RCAInvestigation.version)).where(RCAInvestigation.incident_id == incident_id)
        )
        or 0
    ) + 1

    started = _utc_now()
    investigation = RCAInvestigation(
        incident_id=incident_id,
        status="running",
        version=next_version,
        started_at=started,
        investigation_summary="",
        limitations="Scores indicate evidence strength, not probability. Correlation does not prove causation.",
    )
    db.add(investigation)
    db.flush()

    drafts = generate_candidates(ctx)
    ranked_drafts: list[RankedDraft] = []
    for draft in drafts:
        scored = score_candidate(draft.evidence, settings)
        ranked_drafts.append(
            RankedDraft(
                cause_type=draft.cause_type,
                title=draft.title,
                explanation=build_candidate_explanation(
                    cause_type=draft.cause_type,
                    title=draft.title,
                    support_count=scored.supporting_evidence_count,
                    contradict_count=scored.contradicting_evidence_count,
                ),
                candidate_key=draft.candidate_key,
                service_id=draft.service_id,
                deployment_id=draft.deployment_id,
                confidence_score=scored.confidence_score,
                supporting_evidence_count=scored.supporting_evidence_count,
                contradicting_evidence_count=scored.contradicting_evidence_count,
                evidence_summary=scored.evidence_summary,
            )
        )

    ranked = rank_drafts(ranked_drafts)
    for item in ranked:
        db.add(
            RootCauseCandidate(
                investigation_id=investigation.id,
                incident_id=incident_id,
                service_id=item.service_id,
                deployment_id=item.deployment_id,
                cause_type=item.cause_type,
                title=item.title,
                explanation=item.explanation,
                confidence_score=item.confidence_score,
                ranking=item.ranking,
                evidence_summary=item.evidence_summary,
                supporting_evidence_count=item.supporting_evidence_count,
                contradicting_evidence_count=item.contradicting_evidence_count,
                candidate_key=item.candidate_key,
            )
        )

    status = "completed" if ranked else "insufficient_data"
    if ranked and ranked[0].cause_type == "UNKNOWN" and ranked[0].confidence_score < 20:
        status = "insufficient_data"

    top_title = ranked[0].title if ranked else None
    investigation.status = status
    investigation.completed_at = _utc_now()
    investigation.candidate_count = len(ranked)
    investigation.investigation_summary = build_investigation_summary(ctx, top_title, len(ranked))
    if len(ctx.anomalies) == 0:
        investigation.limitations += " No linked anomalies; conclusions are weak."

    db.commit()
    logger.info(
        "RCA complete incident_id=%s version=%s candidates=%s",
        incident_id,
        next_version,
        len(ranked),
    )
    return {
        "status": status,
        "message": investigation.investigation_summary,
        "investigation_id": str(investigation.id),
        "version": next_version,
        "candidate_count": len(ranked),
        "top_candidate_title": top_title,
        "top_confidence_score": ranked[0].confidence_score if ranked else 0.0,
    }