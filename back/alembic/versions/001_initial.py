"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', postgresql.ENUM('admin', 'manager', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('phone', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False, index=True),
        sa.Column('inn', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50)),
        sa.Column('website', sa.String(500)),
        sa.Column('contact_person', sa.String(255)),
        sa.Column('contact_position', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('status', postgresql.ENUM('active', 'pending', 'blacklist', 'inactive', name='supplier_status'), nullable=False),
        sa.Column('legal_address', sa.Text()),
        sa.Column('actual_address', sa.Text()),
        sa.Column('delivery_regions', postgresql.ARRAY(sa.String())),
        sa.Column('payment_terms', sa.Text()),
        sa.Column('min_order_sum', sa.DECIMAL(12, 2)),
        sa.Column('raw_data_url', sa.String(1000)),
        sa.Column('tags_array', postgresql.ARRAY(sa.String())),
        sa.Column('last_email_sent_at', sa.String()),
        sa.Column('email_thread_id', sa.String(500)),
        sa.Column('import_source', sa.String(50)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Ratings table
    op.create_table(
        'ratings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price_score', sa.Integer(), nullable=False),
        sa.Column('speed_score', sa.Integer(), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Add remaining tables in similar fashion (email_templates, email_campaigns, etc.)
    # This is abbreviated for space - full migration would include all tables


def downgrade() -> None:
    op.drop_table('ratings')
    op.drop_table('suppliers')
    op.drop_table('users')
