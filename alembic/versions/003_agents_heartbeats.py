"""Add agents and heartbeats tables.

Revision ID: 003
Revises: 002
Create Date: 2026-04-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('agent_type', sa.String(20), nullable=False, server_default='general'),
        sa.Column('status', sa.String(20), nullable=False, server_default='idle'),
sa.Column('heartbeat_interval', sa.Integer, nullable=False, server_default="30"),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('missed_heartbeats', sa.Integer, nullable=False, server_default="0"),
        sa.Column('current_task_id', sa.String(36), nullable=True),
        sa.Column('capacity', sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index('ix_agents_status', 'agents', ['status'])

    op.create_table(
        'heartbeats',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('task_id', sa.String(36), nullable=True),
        sa.Column('progress_note', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_heartbeats_timestamp', 'heartbeats', ['timestamp'])


def downgrade() -> None:
    op.drop_table('heartbeats')
    op.drop_table('agents')