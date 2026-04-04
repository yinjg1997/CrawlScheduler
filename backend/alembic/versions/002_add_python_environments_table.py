"""Add python_environments table

Revision ID: 002_add_python_environments_table
Revises: 001_initial
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_python_environments_table'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create python_environments table
    op.create_table(
        'python_environments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_python_environments_id'), 'python_environments', ['id'], unique=False)
    op.create_index(op.f('ix_python_environments_name'), 'python_environments', ['name'], unique=True)
    op.create_index(op.f('ix_python_environments_path'), 'python_environments', ['path'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_python_environments_path'), table_name='python_environments')
    op.drop_index(op.f('ix_python_environments_name'), table_name='python_environments')
    op.drop_index(op.f('ix_python_environments_id'), table_name='python_environments')
    op.drop_table('python_environments')
