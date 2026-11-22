from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from app.core.config import get_settings
from app.modules.root_cause.evidence_collector import InvestigationContext, TraceEvidence


@dataclass
class DraftCandidate:
    cause_type: str
    title: str
    candidate_key: str
    service_id: UUID | None
    deployment_id: UUID | None
    evidence: list[TraceEvidence]


SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _add_unique(bucket: list[TraceEvidence], item: TraceEvidence) -> None:
    if any(existing.evidence_key == item.evidence_key and existing.stance == item.stance for existing in bucket):
        return
    bucket.append(item)


def generate_candidates(ctx: InvestigationContext) -> list[DraftCandidate]:
    settings = get_settings()
    deploy_window = timedelta(minutes=settings.rca_deployment_window_minutes)
    drafts: list[DraftCandidate] = []
    seen_keys: set[str] = set()

    def push(draft: DraftCandidate) -> None:
        if draft.candidate_key in seen_keys:
            return
        seen_keys.add(draft.candidate_key)
        if draft.evidence:
            drafts.append(draft)

    # A. Deployment regression
    for deployment in ctx.deployments:
        evidence: list[TraceEvidence] = []
        related_anomalies = [
            a
            for a in ctx.anomalies
            if a.start_time >= deployment.deployed_at
            and a.start_time - deployment.deployed_at <= deploy_window
            and (deployment.service_id is None or a.service_id == deployment.service_id)
        ]
        pre_anomalies = [
            a
            for a in ctx.anomalies
            if a.start_time < deployment.deployed_at
            and (deployment.service_id is None or a.service_id == deployment.service_id)
        ]

        _add_unique(
            evidence,
            TraceEvidence(
                evidence_key=f"deployment:{deployment.id}",
                source_type="deployment",
                source_id=str(deployment.id),
                timestamp=deployment.deployed_at,
                service_id=deployment.service_id,
                explanation=f"Deployment version {deployment.version} recorded in investigation window.",
                stance="supporting",
                weight_category="deployment",
            ),
        )
        for anomaly in related_anomalies[:5]:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"anomaly:{anomaly.id}",
                    source_type="anomaly",
                    source_id=str(anomaly.id),
                    timestamp=anomaly.start_time,
                    service_id=anomaly.service_id,
                    explanation="Anomaly observed after deployment within correlation window.",
                    stance="supporting",
                    weight_category="temporal",
                ),
            )
            if SEVERITY_RANK.get(anomaly.severity, 0) >= 3:
                _add_unique(
                    evidence,
                    TraceEvidence(
                        evidence_key=f"anomaly_severity:{anomaly.id}",
                        source_type="anomaly",
                        source_id=str(anomaly.id),
                        timestamp=anomaly.start_time,
                        service_id=anomaly.service_id,
                        explanation=f"High severity anomaly ({anomaly.severity}) after deployment.",
                        stance="supporting",
                        weight_category="severity",
                    ),
                )
        if pre_anomalies and not related_anomalies:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"pre_deploy_anomalies:{deployment.id}",
                    source_type="anomaly",
                    source_id=str(pre_anomalies[0].id),
                    timestamp=pre_anomalies[0].start_time,
                    service_id=deployment.service_id,
                    explanation="Anomalies existed before deployment without clear post-deploy increase.",
                    stance="contradicting",
                    weight_category="deployment",
                ),
            )
        if deployment.deployed_at > ctx.incident.last_activity_at:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"deploy_after_incident:{deployment.id}",
                    source_type="deployment",
                    source_id=str(deployment.id),
                    timestamp=deployment.deployed_at,
                    service_id=deployment.service_id,
                    explanation="Deployment occurred after incident activity window.",
                    stance="contradicting",
                    weight_category="temporal",
                ),
            )

        service_name = ctx.services[deployment.service_id].name if deployment.service_id in ctx.services else "project"
        push(
            DraftCandidate(
                cause_type="DEPLOYMENT_REGRESSION",
                title=f"Deployment {deployment.version} may relate to {service_name} failures",
                candidate_key=f"DEPLOYMENT_REGRESSION:{deployment.id}",
                service_id=deployment.service_id,
                deployment_id=deployment.id,
                evidence=evidence,
            )
        )

    # B. Service failure
    for service_id, items in ctx.anomalies_by_service.items():
        if not items:
            continue
        name = ctx.services[service_id].name if service_id and service_id in ctx.services else "unspecified service"
        evidence = []
        error_logs = [log for log in ctx.logs if log.service_id == service_id and log.level in ("ERROR", "CRITICAL")]
        for anomaly in items[:6]:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"anomaly:{anomaly.id}",
                    source_type="anomaly",
                    source_id=str(anomaly.id),
                    timestamp=anomaly.start_time,
                    service_id=service_id,
                    explanation=f"Service-scoped anomaly {anomaly.anomaly_type}.",
                    stance="supporting",
                    weight_category="service",
                ),
            )
        for log in error_logs[:5]:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"log:{log.id}",
                    source_type="log",
                    source_id=str(log.id),
                    timestamp=log.timestamp,
                    service_id=service_id,
                    explanation="Error/critical log on affected service.",
                    stance="supporting",
                    weight_category="error_pattern",
                ),
            )
        if len(items) == 1 and not error_logs:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"sparse_service:{service_id}",
                    source_type="incident",
                    source_id=str(ctx.incident.id),
                    timestamp=ctx.incident.started_at,
                    service_id=service_id,
                    explanation="Limited error signal for isolated anomaly.",
                    stance="contradicting",
                    weight_category="service",
                ),
            )
        push(
            DraftCandidate(
                cause_type="SERVICE_FAILURE",
                title=f"Concentrated failures on service {name}",
                candidate_key=f"SERVICE_FAILURE:{service_id or 'none'}",
                service_id=service_id,
                deployment_id=None,
                evidence=evidence,
            )
        )

    # C. Dependency failure
    for edge in ctx.dependencies:
        up_anomalies = ctx.anomalies_by_service.get(edge.upstream_service_id, [])
        down_anomalies = ctx.anomalies_by_service.get(edge.downstream_service_id, [])
        if not up_anomalies or not down_anomalies:
            continue
        up_name = ctx.services[edge.upstream_service_id].name
        down_name = ctx.services[edge.downstream_service_id].name
        evidence = []
        earliest_up = min(up_anomalies, key=lambda a: a.start_time)
        earliest_down = min(down_anomalies, key=lambda a: a.start_time)
        _add_unique(
            evidence,
            TraceEvidence(
                evidence_key=f"anomaly:{earliest_up.id}",
                source_type="anomaly",
                source_id=str(earliest_up.id),
                timestamp=earliest_up.start_time,
                service_id=edge.upstream_service_id,
                explanation=f"Upstream service {up_name} anomaly precedes downstream activity.",
                stance="supporting",
                weight_category="dependency",
            ),
        )
        _add_unique(
            evidence,
            TraceEvidence(
                evidence_key=f"anomaly:{earliest_down.id}",
                source_type="anomaly",
                source_id=str(earliest_down.id),
                timestamp=earliest_down.start_time,
                service_id=edge.downstream_service_id,
                explanation=f"Downstream service {down_name} errors in shared window.",
                stance="supporting",
                weight_category="dependency",
            ),
        )
        if earliest_down.start_time < earliest_up.start_time:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"down_before_up:{edge.id}",
                    source_type="service_dependency",
                    source_id=str(edge.id),
                    timestamp=earliest_down.start_time,
                    service_id=edge.downstream_service_id,
                    explanation="Downstream anomalies began before upstream anomalies (weakens upstream hypothesis).",
                    stance="contradicting",
                    weight_category="dependency",
                ),
            )
        push(
            DraftCandidate(
                cause_type="DEPENDENCY_FAILURE",
                title=f"Possible upstream impact: {up_name} → {down_name}",
                candidate_key=f"DEPENDENCY_FAILURE:{edge.id}",
                service_id=edge.upstream_service_id,
                deployment_id=None,
                evidence=evidence,
            )
        )

    # D. Error pattern (clusters)
    for cluster in ctx.clusters:
        if cluster.log_count < 2:
            continue
        evidence = []
        _add_unique(
            evidence,
            TraceEvidence(
                evidence_key=f"cluster:{cluster.id}",
                source_type="log_cluster",
                source_id=str(cluster.id),
                timestamp=cluster.last_seen,
                service_id=None,
                explanation=f"Repeated pattern ({cluster.log_count} logs): {cluster.representative_message[:200]}",
                stance="supporting",
                weight_category="error_pattern",
            ),
        )
        push(
            DraftCandidate(
                cause_type="ERROR_PATTERN",
                title=f"Repeated error pattern {cluster.cluster_label}",
                candidate_key=f"ERROR_PATTERN:{cluster.id}",
                service_id=ctx.incident.primary_service_id,
                deployment_id=None,
                evidence=evidence,
            )
        )

    # E. Traffic anomaly
    traffic_types = {"log_volume_spike", "error_ratio_spike", "multivariate_pattern"}
    traffic_anomalies = [a for a in ctx.anomalies if a.anomaly_type in traffic_types]
    if traffic_anomalies:
        evidence = []
        for anomaly in traffic_anomalies[:5]:
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"anomaly:{anomaly.id}",
                    source_type="anomaly",
                    source_id=str(anomaly.id),
                    timestamp=anomaly.start_time,
                    service_id=anomaly.service_id,
                    explanation=f"Traffic/volume anomaly ({anomaly.anomaly_type}).",
                    stance="supporting",
                    weight_category="traffic",
                ),
            )
        push(
            DraftCandidate(
                cause_type="TRAFFIC_ANOMALY",
                title="Abnormal log volume or error ratio",
                candidate_key="TRAFFIC_ANOMALY:aggregate",
                service_id=ctx.incident.primary_service_id,
                deployment_id=None,
                evidence=evidence,
            )
        )

    # F. Configuration change via deployment diff
    for deployment in ctx.deployments:
        if not deployment.configuration_diff:
            continue
        evidence = [
            TraceEvidence(
                evidence_key=f"config_diff:{deployment.id}",
                source_type="deployment",
                source_id=str(deployment.id),
                timestamp=deployment.deployed_at,
                service_id=deployment.service_id,
                explanation="Non-secret configuration fields changed at deployment.",
                stance="supporting",
                weight_category="deployment",
            )
        ]
        push(
            DraftCandidate(
                cause_type="CONFIGURATION_CHANGE",
                title=f"Configuration change in deployment {deployment.version}",
                candidate_key=f"CONFIGURATION_CHANGE:{deployment.id}",
                service_id=deployment.service_id,
                deployment_id=deployment.id,
                evidence=evidence,
            )
        )

    if not drafts:
        evidence = []
        if ctx.anomalies:
            a = ctx.anomalies[0]
            _add_unique(
                evidence,
                TraceEvidence(
                    evidence_key=f"anomaly:{a.id}",
                    source_type="anomaly",
                    source_id=str(a.id),
                    timestamp=a.start_time,
                    service_id=a.service_id,
                    explanation="Limited evidence available for strong hypothesis.",
                    stance="supporting",
                    weight_category="general",
                ),
            )
        drafts.append(
            DraftCandidate(
                cause_type="UNKNOWN",
                title="Insufficient evidence for a specific root cause",
                candidate_key="UNKNOWN:default",
                service_id=ctx.incident.primary_service_id,
                deployment_id=None,
                evidence=evidence,
            )
        )

    return drafts