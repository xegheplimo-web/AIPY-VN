"""add promotions and reports

Revision ID: add_promotions_reports
Revises: b8f3d2e1c4a5
Create Date: 2024-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_promotions_reports'
down_revision: Union[str, None] = 'b8f3d2e1c4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create promotions table
    op.create_table(
        'promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('value', sa.DECIMAL(12, 2)),
        sa.Column('min_order_amount', sa.DECIMAL(12, 2), server_default='0'),
        sa.Column('max_discount', sa.DECIMAL(12, 2)),
        sa.Column('usage_limit', sa.Integer()),
        sa.Column('used_count', sa.Integer(), server_default='0'),
        sa.Column('start_date', sa.String(), nullable=False),
        sa.Column('end_date', sa.String(), nullable=False),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('applicable_stores', sa.JSON()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.String(), server_default='now()'),
        sa.Column('updated_at', sa.String(), server_default='now()'),
    )
    op.create_index('idx_promotion_code', 'promotions', ['code'], unique=True)
    op.create_index('idx_promotion_status', 'promotions', ['status'])
    op.create_index('idx_promotion_dates', 'promotions', ['start_date', 'end_date'])
    op.create_foreign_key('fk_promotions_created_by', 'promotions', 'users', ['created_by'], ['id'])

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_name', sa.String(200)),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('reporter_name', sa.String(100)),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('evidence', sa.JSON()),
        sa.Column('resolution_notes', sa.Text()),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('resolved_at', sa.String()),
        sa.Column('created_at', sa.String(), server_default='now()'),
    )
    op.create_index('idx_report_type', 'reports', ['type'])
    op.create_index('idx_report_status', 'reports', ['status'])
    op.create_index('idx_report_target', 'reports', ['target_id'])
    op.create_index('idx_report_reporter', 'reports', ['reporter_id'])
    op.create_foreign_key('fk_reports_reporter_id', 'reports', 'users', ['reporter_id'], ['id'])
    op.create_foreign_key('fk_reports_resolved_by', 'reports', 'users', ['resolved_by'], ['id'])


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('promotions')
