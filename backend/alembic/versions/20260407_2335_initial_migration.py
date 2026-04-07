"""Initial migration

Revision ID: initial
Revises:
Create Date: 2026-04-07 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create projects table
    op.create_table('projects',
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('working_directory', sa.String(length=500), nullable=False),
        sa.Column('python_executable', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_name', 'projects', ['name'], unique=True)
    op.create_index('ix_projects_id', 'projects', ['id'], unique=False)

    # Create crawlers table
    op.create_table('crawlers',
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('command', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crawlers_name', 'crawlers', ['name'], unique=True)
    op.create_index('ix_crawlers_id', 'crawlers', ['id'], unique=False)

    # Create schedules table
    op.create_table('schedules',
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('crawler_id', sa.Integer(), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('next_run_time', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crawler_id'], ['crawlers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_schedules_name', 'schedules', ['name'], unique=True)
    op.create_index('ix_schedules_id', 'schedules', ['id'], unique=False)

    # Create task_executions table
    op.create_table('task_executions',
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
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['crawler_id'], ['crawlers.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_executions_status', 'task_executions', ['status'], unique=False)
    op.create_index('ix_task_executions_id', 'task_executions', ['id'], unique=False)


def downgrade() -> None:
    # Drop in reverse order of creation
    op.drop_index('ix_task_executions_id', table_name='task_executions')
    op.drop_index('ix_task_executions_status', table_name='task_executions')
    op.drop_table('task_executions')

    op.drop_index('ix_schedules_id', table_name='schedules')
    op.drop_index('ix_schedules_name', table_name='schedules')
    op.drop_table('schedules')

    op.drop_index('ix_crawlers_id', table_name='crawlers')
    op.drop_index('ix_crawlers_name', table_name='crawlers')
    op.drop_table('crawlers')

    op.drop_index('ix_projects_id', table_name='projects')
    op.drop_index('ix_projects_name', table_name='projects')
    op.drop_table('projects')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
