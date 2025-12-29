"""add supplier color

Revision ID: add_supplier_color
Revises: 
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_supplier_color'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('suppliers', sa.Column('color', sa.String(7), nullable=True, server_default='#3B82F6'))

def downgrade():
    op.drop_column('suppliers', 'color')
