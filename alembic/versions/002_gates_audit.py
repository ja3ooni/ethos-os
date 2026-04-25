"""Phase 2 migration - gates and audit log.

Revision ID: 002
Revises: 001
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Gate requests table
    op.create_table(
        "gate_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("gate_type", sa.String(20), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("trigger_condition", sa.Text, nullable=True),
        sa.Column("approver", sa.String(36), nullable=True),
        sa.Column("decision_notes", sa.Text, nullable=True),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timeout_hours", sa.Integer, nullable=False, default=48),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )

    # Audit log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=True),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("gate_requests")