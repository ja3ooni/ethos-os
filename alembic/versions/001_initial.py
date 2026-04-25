"""Initial schema - portfolio, program, project, sprint, task, prd

Revision ID: 001
Revises: 
Create Date: 2026-04-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('strategic_intent', sa.Text, nullable=True),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('path', sa.String(500), nullable=False, default=''),
        sa.Column('path_depth', sa.Integer, nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    op.create_index('ix_portfolios_path', 'portfolios', ['path'])
    op.create_index('ix_portfolios_path_depth', 'portfolios', ['path_depth'])
    
    # Programs table
    op.create_table(
        'programs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('path_depth', sa.Integer, nullable=False, default=2),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    op.create_index('ix_programs_path', 'programs', ['path'])
    op.create_index('ix_programs_path_depth', 'programs', ['path_depth'])
    op.create_index('ix_programs_portfolio_id', 'programs', ['portfolio_id'])
    
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('program_id', sa.String(36), sa.ForeignKey('programs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prd_status', sa.String(20), nullable=False, default='draft'),
        sa.Column('intent', sa.Text, nullable=True),
        sa.Column('success_metric', sa.Text, nullable=True),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('boundaries', sa.Text, nullable=True),
        sa.Column('timeline', sa.Text, nullable=True),  # JSON as text for SQLite
        sa.Column('budget', sa.Integer, nullable=True),
        sa.Column('qdrant_collection_name', sa.String(255), nullable=True),
        sa.Column('qdrant_point_id', sa.String(36), nullable=True),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('path_depth', sa.Integer, nullable=False, default=3),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    op.create_index('ix_projects_path', 'projects', ['path'])
    op.create_index('ix_projects_path_depth', 'projects', ['path_depth'])
    op.create_index('ix_projects_program_id', 'projects', ['program_id'])
    op.create_index('ix_projects_prd_status', 'projects', ['prd_status'])
    
    # Sprints table
    op.create_table(
        'sprints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal', sa.Text, nullable=True),
        sa.Column('start_date', sa.Text, nullable=True),
        sa.Column('end_date', sa.Text, nullable=True),
        sa.Column('capacity_hours', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='planning'),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('path_depth', sa.Integer, nullable=False, default=4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    op.create_index('ix_sprints_path', 'sprints', ['path'])
    op.create_index('ix_sprints_path_depth', 'sprints', ['path_depth'])
    op.create_index('ix_sprints_project_id', 'sprints', ['project_id'])
    op.create_index('ix_sprints_status', 'sprints', ['status'])
    
    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('sprint_id', sa.String(36), sa.ForeignKey('sprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prd_scope_item_id', sa.String(36), nullable=False),
        sa.Column('effort_estimate_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('assignee_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='todo'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('path_depth', sa.Integer, nullable=False, default=5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('owner_id', sa.String(36), nullable=True),
    )
    op.create_index('ix_tasks_path', 'tasks', ['path'])
    op.create_index('ix_tasks_path_depth', 'tasks', ['path_depth'])
    op.create_index('ix_tasks_sprint_id', 'tasks', ['sprint_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_prd_scope_item_id', 'tasks', ['prd_scope_item_id'])
    
    # PRDs table
    op.create_table(
        'prds',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('intent', sa.Text, nullable=False),
        sa.Column('success_metric', sa.Text, nullable=False),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('boundaries', sa.Text, nullable=True),
        sa.Column('timeline', sa.Text, nullable=True),
        sa.Column('budget', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('qdrant_collection_name', sa.String(255), nullable=True),
        sa.Column('qdrant_point_id', sa.String(36), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('reviewed_by', sa.String(36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_prds_project_id', 'prds', ['project_id'])
    op.create_index('ix_prds_status', 'prds', ['status'])


def downgrade() -> None:
    op.drop_table('prds')
    op.drop_table('tasks')
    op.drop_table('sprints')
    op.drop_table('projects')
    op.drop_table('programs')
    op.drop_table('portfolios')