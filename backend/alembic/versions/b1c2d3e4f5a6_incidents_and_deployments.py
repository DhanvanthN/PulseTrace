"""incidents_and_deployments

Revision ID: b1c2d3e4f5a6
Revises: 8f3a2c1d4e5b
Create Date: 2026-11-20 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "8f3a2c1d4e5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_dependencies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("upstream_service_id", sa.UUID(), nullable=False),
        sa.Column("downstream_service_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["downstream_service_id"], ["services.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upstream_service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "upstream_service_id",
            "downstream_service_id",
            name="uq_service_dependencies_pair",
        ),
    )
    op.create_index(
        op.f("ix_service_dependencies_downstream_service_id"),
        "service_dependencies",
        ["downstream_service_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_dependencies_upstream_service_id"),
        "service_dependencies",
        ["upstream_service_id"],
        unique=False,
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("primary_service_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["primary_service_id"], ["services.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "correlation_key", name="uq_incidents_project_correlation_key"),
    )
    op.create_index(op.f("ix_incidents_project_id"), "incidents", ["project_id"], unique=False)
    op.create_index(op.f("ix_incidents_primary_service_id"), "incidents", ["primary_service_id"], unique=False)
    op.create_index(op.f("ix_incidents_severity"), "incidents", ["severity"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)
    op.create_index(op.f("ix_incidents_started_at"), "incidents", ["started_at"], unique=False)
    op.create_index(op.f("ix_incidents_last_activity_at"), "incidents", ["last_activity_at"], unique=False)
    op.create_index("ix_incidents_project_status", "incidents", ["project_id", "status"], unique=False)
    op.create_index("ix_incidents_project_severity", "incidents", ["project_id", "severity"], unique=False)
    op.create_index("ix_incidents_last_activity", "incidents", ["project_id", "last_activity_at"], unique=False)

    op.create_table(
        "incident_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("incident_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id", "dedupe_key", name="uq_incident_events_incident_dedupe"),
    )
    op.create_index(op.f("ix_incident_events_incident_id"), "incident_events", ["incident_id"], unique=False)
    op.create_index(op.f("ix_incident_events_event_type"), "incident_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_incident_events_event_timestamp"), "incident_events", ["event_timestamp"], unique=False)
    op.create_index(
        "ix_incident_events_incident_time",
        "incident_events",
        ["incident_id", "event_timestamp"],
        unique=False,
    )

    op.create_table(
        "incident_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("incident_id", sa.UUID(), nullable=False),
        sa.Column("log_id", sa.UUID(), nullable=True),
        sa.Column("anomaly_id", sa.UUID(), nullable=True),
        sa.Column("cluster_id", sa.UUID(), nullable=True),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(CASE WHEN log_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN anomaly_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN cluster_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="ck_incident_evidence_at_least_one_ref",
        ),
        sa.ForeignKeyConstraint(["anomaly_id"], ["anomalies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cluster_id"], ["log_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["log_id"], ["logs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incident_evidence_incident_id"), "incident_evidence", ["incident_id"], unique=False)
    op.create_index(op.f("ix_incident_evidence_log_id"), "incident_evidence", ["log_id"], unique=False)
    op.create_index(op.f("ix_incident_evidence_anomaly_id"), "incident_evidence", ["anomaly_id"], unique=False)
    op.create_index(op.f("ix_incident_evidence_cluster_id"), "incident_evidence", ["cluster_id"], unique=False)
    op.create_index("ix_incident_evidence_incident", "incident_evidence", ["incident_id"], unique=False)

    op.create_table(
        "deployments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.String(length=128), nullable=False),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("configuration_diff", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deployments_project_id"), "deployments", ["project_id"], unique=False)
    op.create_index(op.f("ix_deployments_service_id"), "deployments", ["service_id"], unique=False)
    op.create_index(op.f("ix_deployments_deployed_at"), "deployments", ["deployed_at"], unique=False)
    op.create_index("ix_deployments_project_deployed", "deployments", ["project_id", "deployed_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_deployments_project_deployed", table_name="deployments")
    op.drop_index(op.f("ix_deployments_deployed_at"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_service_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_project_id"), table_name="deployments")
    op.drop_table("deployments")
    op.drop_index("ix_incident_evidence_incident", table_name="incident_evidence")
    op.drop_index(op.f("ix_incident_evidence_cluster_id"), table_name="incident_evidence")
    op.drop_index(op.f("ix_incident_evidence_anomaly_id"), table_name="incident_evidence")
    op.drop_index(op.f("ix_incident_evidence_log_id"), table_name="incident_evidence")
    op.drop_index(op.f("ix_incident_evidence_incident_id"), table_name="incident_evidence")
    op.drop_table("incident_evidence")
    op.drop_index("ix_incident_events_incident_time", table_name="incident_events")
    op.drop_index(op.f("ix_incident_events_event_timestamp"), table_name="incident_events")
    op.drop_index(op.f("ix_incident_events_event_type"), table_name="incident_events")
    op.drop_index(op.f("ix_incident_events_incident_id"), table_name="incident_events")
    op.drop_table("incident_events")
    op.drop_index("ix_incidents_last_activity", table_name="incidents")
    op.drop_index("ix_incidents_project_severity", table_name="incidents")
    op.drop_index("ix_incidents_project_status", table_name="incidents")
    op.drop_index(op.f("ix_incidents_last_activity_at"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_started_at"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_severity"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_primary_service_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_project_id"), table_name="incidents")
    op.drop_table("incidents")
    op.drop_index(op.f("ix_service_dependencies_upstream_service_id"), table_name="service_dependencies")
    op.drop_index(op.f("ix_service_dependencies_downstream_service_id"), table_name="service_dependencies")
    op.drop_table("service_dependencies")