"""add smtp settings to users

Revision ID: add_smtp_to_users
Revises: 
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('smtp_host', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('smtp_port', sa.Integer(), nullable=True, server_default='587'))
    op.add_column('users', sa.Column('smtp_user', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('smtp_password', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('smtp_use_tls', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('users', sa.Column('smtp_from_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_signature', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('email_default_subject', sa.String(500), nullable=True))

def downgrade():
    op.drop_column('users', 'smtp_host')
    op.drop_column('users', 'smtp_port')
    op.drop_column('users', 'smtp_user')
    op.drop_column('users', 'smtp_password')
    op.drop_column('users', 'smtp_use_tls')
    op.drop_column('users', 'smtp_from_name')
    op.add_column('users', 'email_signature')
    op.drop_column('users', 'email_default_subject')
