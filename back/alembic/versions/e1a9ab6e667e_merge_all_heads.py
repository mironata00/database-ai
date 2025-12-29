"""merge_all_heads

Revision ID: e1a9ab6e667e
Revises: 001_initial, 20251228160000
Create Date: 2025-12-29 13:27:16.545791

"""
from alembic import op
import sqlalchemy as sa


revision = 'e1a9ab6e667e'
down_revision = ('001_initial', '20251228160000')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
