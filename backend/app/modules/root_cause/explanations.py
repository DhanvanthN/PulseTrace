from __future__ import annotations

from app.modules.root_cause.evidence_collector import InvestigationContext


def build_candidate_explanation(*, cause_type: str, title: str, support_count: int, contradict_count: int) -> str:
    return (
        f"Hypothesis ({cause_type}): {title}. "
        f"Based on {support_count} supporting and {contradict_count} contradicting evidence item(s). "
        "This ranks plausible explanations from observed data; it does not prove causation."
    )


def build_investigation_summary(ctx: InvestigationContext, top_title: str | None, candidate_count: int) -> str:
    if candidate_count == 0:
        return (
            "Investigation completed with insufficient evidence to rank root cause candidates. "
            "Collect more logs, anomalies, or deployment records."
        )
    lead = top_title or "No ranked candidate"
    return (
        f"Investigation analyzed {len(ctx.anomalies)} anomalies, {len(ctx.logs)} logs, "
        f"{len(ctx.clusters)} clusters, and {len(ctx.deployments)} deployments. "
        f"Strongest supported hypothesis: {lead} (evidence strength ranking, not proven root cause)."
    )