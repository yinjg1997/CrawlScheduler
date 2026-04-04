"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2025-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crawlers table
    op.create_table(
        'crawlers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('command', sa.String(length=500), nullable=False),
        sa.Column('working_directory', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('python_executable', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawlers_id'), 'crawlers', ['id'], unique=False)
    op.create_index(op.f('ix_crawlers_name'), 'crawlers', ['name'], unique=True)

    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('crawler_id', sa.Integer(), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('next_run_time', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crawler_id'], ['crawlers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)
    op.create_index(op.f('ix_schedules_name'), 'schedules', ['name'], unique=False)

    # Create task_executions table
    op.create_table(
        'task_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('crawler_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('log_file_path', sa.String(length=500), nullable=True),
        sa.Column('triggered_by', sa.String(length=50), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crawler_id'], ['crawlers.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_executions_id'), 'task_executions', ['id'], unique=False)
    op.create_index(op.f('ix_task_executions_status'), 'task_executions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_task_executions_status'), table_name='task_executions')
    op.drop_index(op.f('ix_task_executions_id'), table_name='task_executions')
    op.drop_table('task_executions')

    op.drop_index(op.f('ix_schedules_name'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
    op.drop_table('schedules')

    op.drop_index(op.f('ix_crawlers_name'), table_name='crawlers')
    op.drop_index(op.f('ix_crawlers_id'), table_name='crawlers')
    op.drop_table('crawlers')
