"""seed test suppliers data

Revision ID: seed_001
Revises: 
Create Date: 2025-12-26 18:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'seed_001'
down_revision = None
depends_on = None


def upgrade():
    # Create tables first
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.Enum('admin', 'manager', 'viewer', name='userrole'), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('company_name', sa.String(500), nullable=False, index=True),
        sa.Column('inn', sa.String(12), nullable=False, unique=True, index=True),
        sa.Column('kpp', sa.String(9)),
        sa.Column('ogrn', sa.String(15)),
        sa.Column('legal_address', sa.Text()),
        sa.Column('actual_address', sa.Text()),
        sa.Column('email', sa.String(255), index=True),
        sa.Column('phone', sa.String(50)),
        sa.Column('website', sa.String(500)),
        sa.Column('contact_person', sa.String(255)),
        sa.Column('rating', sa.Float(), server_default='0.0'),
        sa.Column('is_blacklisted', sa.Boolean(), server_default='false'),
        sa.Column('blacklist_reason', sa.Text()),
        sa.Column('tags_array', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_activity_at', sa.DateTime()),
    )

    # Insert test users
    op.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
        VALUES 
        ('{}', 'admin@company.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRGhTqW', 'Алексей (Админ)', 'admin', true),
        ('{}', 'manager@company.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLRGhTqW', 'Мария (Менеджер)', 'manager', true)
    """.format(uuid.uuid4(), uuid.uuid4()))

    # Insert test suppliers
    suppliers = [
        {
            'id': str(uuid.uuid4()),
            'company_name': 'СтройКомплект',
            'inn': '7701234567',
            'email': 'info@stroykomplekt.ru',
            'rating': 4.3,
            'is_blacklisted': False,
            'tags_array': ['Цемент', 'Knauf', 'Сухие смеси', 'Бетон']
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'ЭлектроМир',
            'inn': '7709876543',
            'email': 'sales@electromir.ru',
            'rating': 4.3,
            'is_blacklisted': False,
            'tags_array': ['ABB', 'Schneider', 'Кабель', 'Розетки', 'Электрика']
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'Рога и Копыта',
            'inn': '7700000000',
            'email': 'scam@example.com',
            'rating': 1.0,
            'is_blacklisted': True,
            'blacklist_reason': 'Мошенничество, не доставили товар',
            'tags_array': ['Воздух']
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'ООО',
            'inn': '7724422835',
            'email': 'simon-15@list.ru',
            'rating': 0.0,
            'is_blacklisted': False,
            'tags_array': ['Заявка на', 'Градация']
        },
    ]

    for supplier in suppliers:
        tags_str = '{' + ','.join([f'"{tag}"' for tag in supplier['tags_array']]) + '}'
        op.execute(f"""
            INSERT INTO suppliers (id, company_name, inn, email, rating, is_blacklisted, blacklist_reason, tags_array)
            VALUES (
                '{supplier['id']}',
                '{supplier['company_name']}',
                '{supplier['inn']}',
                '{supplier['email']}',
                {supplier['rating']},
                {supplier['is_blacklisted']},
                {'NULL' if not supplier.get('blacklist_reason') else f"'{supplier['blacklist_reason']}'"},
                '{tags_str}'
            )
        """)


def downgrade():
    op.drop_table('suppliers')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS userrole')
