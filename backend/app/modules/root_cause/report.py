from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.rca import RCAInvestigation, RootCauseCandidate
from app.models.service import Service
from app.modules.root_cause.evidence_collector import collect_investigation_context
from app.repositories.incident_repository import IncidentRepository


def build_investigation_report(db: Session, *, project_id: UUID, incident_id: UUID) -> dict | None:
    incident = IncidentRepository(db).get_in_project(incident_id, project_id)
    if incident is None:
        return None

    investigation = db.scalars(
        select(RCAInvestigation)
        .where(RCAInvestigation.incident_id == incident_id)
        .order_by(RCAInvestigation.version.desc())
        .limit(1)
    ).first()

    candidates = []
    if investigation:
        candidates = list(
            db.scalars(
                select(RootCauseCandidate)
                .where(RootCauseCandidate.investigation_id == investigation.id)
                .order_by(RootCauseCandidate.ranking.asc())
            ).all()
        )

    ctx = collect_investigation_context(db, project_id=project_id, incident_id=incident_id)
    services = []
    if ctx:
        service_ids = {incident.primary_service_id, *(a.service_id for a in ctx.anomalies)}
        service_ids.discard(None)
        if service_ids:
            services = [
                {"id": str(row.id), "name": row.name}
                for row in db.scalars(select(Service).where(Service.id.in_(service_ids))).all()
            ]

    timeline = IncidentRepository(db).timeline(incident_id)
    anomaly_findings = []
    if ctx:
        for anomaly in ctx.anomalies[:20]:
            anomaly_findings.append(
                {
                    "id": str(anomaly.id),
                    "type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "start_time": anomaly.start_time.isoformat(),
                    "measurements": anomaly.evidence,
                }
            )

    top = candidates[0] if candidates else None
    conclusion = (
        f"Strongest supported hypothesis: {top.title} (evidence strength {top.confidence_score:.1f}/100)."
        if top and top.cause_type != "UNKNOWN"
        else "Insufficient evidence to support a specific root cause hypothesis."
    )

    recommendations = []
    if top and top.cause_type == "DEPLOYMENT_REGRESSION":
        recommendations.append(
            "Review deployment diffs and error rates after release (recommendation, not verified finding)."
        )
    if top and top.cause_type in {"SERVICE_FAILURE", "DEPENDENCY_FAILURE"}:
        recommendations.append("Inspect service health checks and dependency traces for corroboration.")
    if not recommendations:
        recommendations.append("Continue collecting logs and anomalies, then re-run investigation.")

    return {
        "incident_overview": {
            "title": incident.title,
            "severity": incident.severity,
            "status": incident.status,
            "started_at": incident.started_at.isoformat(),
            "affected_services": services,
        },
        "executive_summary": investigation.investigation_summary if investigation else incident.description,
        "timeline": [
            {
                "event_type": event.event_type,
                "timestamp": event.event_timestamp.isoformat(),
                "description": event.description,
                "metadata": event.event_metadata,
            }
            for event in timeline
        ],
        "anomaly_findings": anomaly_findings,
        "root_cause_candidates": [
            {
                "ranking": item.ranking,
                "cause_type": item.cause_type,
                "title": item.title,
                "confidence_score": item.confidence_score,
                "score_note": item.evidence_summary.get("score_note"),
                "supporting_evidence_count": item.supporting_evidence_count,
                "contradicting_evidence_count": item.contradicting_evidence_count,
            }
            for item in candidates
        ],
        "supporting_evidence": [
            row
            for item in candidates
            for row in item.evidence_summary.get("items", [])
            if row.get("stance") == "supporting"
        ],
        "contradicting_evidence": [
            row
            for item in candidates
            for row in item.evidence_summary.get("items", [])
            if row.get("stance") == "contradicting"
        ],
        "service_impact": {
            "services": services,
            "dependency_note": "Dependency relationships are correlational, not causal proof.",
        },
        "investigation_conclusion": conclusion,
        "recommended_next_steps": recommendations,
        "investigation_meta": {
            "investigation_id": str(investigation.id) if investigation else None,
            "version": investigation.version if investigation else None,
            "status": investigation.status if investigation else "not_run",
            "limitations": investigation.limitations if investigation else None,
        },
        "export_markdown_available": True,
    }


def report_to_markdown(report: dict) -> str:
    lines = [
        f"# Investigation Report: {report['incident_overview']['title']}",
        "",
        "## Executive summary",
        report["executive_summary"],
        "",
        "## Conclusion",
        report["investigation_conclusion"],
        "",
        "## Root cause candidates",
    ]
    for item in report["root_cause_candidates"]:
        lines.append(
            f"- #{item['ranking']} {item['title']} ({item['cause_type']}) — "
            f"evidence strength {item['confidence_score']} (not probability)"
        )
    lines.extend(["", "## Recommended next steps"])
    lines.extend(f"- {step}" for step in report["recommended_next_steps"])
    return "\n".join(lines)