"""anomalies_and_log_clusters

Revision ID: 8f3a2c1d4e5b
Revises: 577bfbf39056
Create Date: 2026-11-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8f3a2c1d4e5b"
down_revision: Union[str, None] = "577bfbf39056"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anomalies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("anomaly_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detection_method", sa.String(length=64), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "dedupe_key", name="uq_anomalies_project_dedupe"),
    )
    op.create_index(op.f("ix_anomalies_project_id"), "anomalies", ["project_id"], unique=False)
    op.create_index(op.f("ix_anomalies_service_id"), "anomalies", ["service_id"], unique=False)
    op.create_index(op.f("ix_anomalies_severity"), "anomalies", ["severity"], unique=False)
    op.create_index(op.f("ix_anomalies_start_time"), "anomalies", ["start_time"], unique=False)
    op.create_index("ix_anomalies_project_severity", "anomalies", ["project_id", "severity"], unique=False)
    op.create_index("ix_anomalies_project_type", "anomalies", ["project_id", "anomaly_type"], unique=False)

    op.create_table(
        "log_clusters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("cluster_label", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("representative_message", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(length=64), nullable=False),
        sa.Column("log_count", sa.Integer(), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "cluster_label", name="uq_log_clusters_project_label"),
    )
    op.create_index(op.f("ix_log_clusters_project_id"), "log_clusters", ["project_id"], unique=False)

    op.create_table(
        "log_cluster_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cluster_id", sa.UUID(), nullable=False),
        sa.Column("log_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["log_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["log_id"], ["logs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("log_id", "cluster_id", name="uq_cluster_membership_log_cluster"),
    )
    op.create_index(op.f("ix_log_cluster_memberships_cluster_id"), "log_cluster_memberships", ["cluster_id"], unique=False)
    op.create_index(op.f("ix_log_cluster_memberships_log_id"), "log_cluster_memberships", ["log_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_log_cluster_memberships_log_id"), table_name="log_cluster_memberships")
    op.drop_index(op.f("ix_log_cluster_memberships_cluster_id"), table_name="log_cluster_memberships")
    op.drop_table("log_cluster_memberships")
    op.drop_index(op.f("ix_log_clusters_project_id"), table_name="log_clusters")
    op.drop_table("log_clusters")
    op.drop_index("ix_anomalies_project_type", table_name="anomalies")
    op.drop_index("ix_anomalies_project_severity", table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_start_time"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_severity"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_service_id"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_project_id"), table_name="anomalies")
    op.drop_table("anomalies")