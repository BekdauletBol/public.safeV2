"""Initial migration

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'cameras',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('stream_url', sa.Text(), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_connected', sa.Boolean(), default=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('fps', sa.Integer(), default=15),
        sa.Column('resolution_width', sa.Integer(), default=1280),
        sa.Column('resolution_height', sa.Integer(), default=720),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )

    op.create_table(
        'roi_configs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('cameras.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('x', sa.Float(), default=0.0),
        sa.Column('y', sa.Float(), default=0.0),
        sa.Column('width', sa.Float(), default=1.0),
        sa.Column('height', sa.Float(), default=1.0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'analytics_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('people_count', sa.Integer(), default=0),
        sa.Column('confidence_avg', sa.Float(), default=0.0),
        sa.Column('period_type', sa.String(20), default='realtime'),
    )
    op.create_index('idx_analytics_camera_ts', 'analytics_records', ['camera_id', sa.text('timestamp DESC')])

    op.create_table(
        'hourly_aggregates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hour_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_count', sa.Integer(), default=0),
        sa.Column('avg_count', sa.Float(), default=0.0),
        sa.Column('max_count', sa.Integer(), default=0),
        sa.Column('min_count', sa.Integer(), default=0),
        sa.Column('sample_count', sa.Integer(), default=0),
    )

    op.create_table(
        'daily_aggregates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('camera_id', sa.Integer(), sa.ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_count', sa.Integer(), default=0),
        sa.Column('avg_count', sa.Float(), default=0.0),
        sa.Column('max_count', sa.Integer(), default=0),
        sa.Column('peak_hour', sa.Integer(), nullable=True),
    )

    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('report_type', sa.String(50), default='weekly'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_format', sa.String(10), default='pdf'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('ai_insights', sa.Text(), nullable=True),
        sa.Column('is_reset_done', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('reports')
    op.drop_table('daily_aggregates')
    op.drop_table('hourly_aggregates')
    op.drop_index('idx_analytics_camera_ts', 'analytics_records')
    op.drop_table('analytics_records')
    op.drop_table('roi_configs')
    op.drop_table('cameras')
    op.drop_table('users')
