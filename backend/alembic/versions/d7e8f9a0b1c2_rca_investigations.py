"""rca_investigations

Revision ID: d7e8f9a0b1c2
Revises: b1c2d3e4f5a6
Create Date: 2026-11-20 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rca_investigations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("incident_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("investigation_summary", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id", "version", name="uq_rca_investigations_incident_version"),
    )
    op.create_index(op.f("ix_rca_investigations_incident_id"), "rca_investigations", ["incident_id"], unique=False)
    op.create_index("ix_rca_investigations_incident", "rca_investigations", ["incident_id", "version"], unique=False)

    op.create_table(
        "root_cause_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("investigation_id", sa.UUID(), nullable=False),
        sa.Column("incident_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("deployment_id", sa.UUID(), nullable=True),
        sa.Column("cause_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("ranking", sa.Integer(), nullable=False),
        sa.Column("evidence_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("supporting_evidence_count", sa.Integer(), nullable=False),
        sa.Column("contradicting_evidence_count", sa.Integer(), nullable=False),
        sa.Column("candidate_key", sa.String(length=192), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["investigation_id"], ["rca_investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investigation_id", "candidate_key", name="uq_rca_candidate_investigation_key"),
    )
    op.create_index(op.f("ix_root_cause_candidates_investigation_id"), "root_cause_candidates", ["investigation_id"], unique=False)
    op.create_index(op.f("ix_root_cause_candidates_incident_id"), "root_cause_candidates", ["incident_id"], unique=False)
    op.create_index(op.f("ix_root_cause_candidates_service_id"), "root_cause_candidates", ["service_id"], unique=False)
    op.create_index(op.f("ix_root_cause_candidates_deployment_id"), "root_cause_candidates", ["deployment_id"], unique=False)
    op.create_index(op.f("ix_root_cause_candidates_cause_type"), "root_cause_candidates", ["cause_type"], unique=False)
    op.create_index("ix_root_cause_candidates_incident_rank", "root_cause_candidates", ["incident_id", "ranking"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_root_cause_candidates_incident_rank", table_name="root_cause_candidates")
    op.drop_index(op.f("ix_root_cause_candidates_cause_type"), table_name="root_cause_candidates")
    op.drop_index(op.f("ix_root_cause_candidates_deployment_id"), table_name="root_cause_candidates")
    op.drop_index(op.f("ix_root_cause_candidates_service_id"), table_name="root_cause_candidates")
    op.drop_index(op.f("ix_root_cause_candidates_incident_id"), table_name="root_cause_candidates")
    op.drop_index(op.f("ix_root_cause_candidates_investigation_id"), table_name="root_cause_candidates")
    op.drop_table("root_cause_candidates")
    op.drop_index("ix_rca_investigations_incident", table_name="rca_investigations")
    op.drop_index(op.f("ix_rca_investigations_incident_id"), table_name="rca_investigations")
    op.drop_table("rca_investigations")