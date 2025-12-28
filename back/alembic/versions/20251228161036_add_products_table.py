"""add products table

Revision ID: 20251228160000
Revises: seed_001
Create Date: 2025-12-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20251228160000'
down_revision = 'seed_001'
branch_labels = None
depends_on = None


def upgrade():
    # Создание таблицы products
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('import_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        sa.Column('sku', sa.String(length=255), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('brand', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('old_price', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=True),
        sa.Column('min_order', sa.Float(), nullable=True),
        
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('specifications', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('vendor_code', sa.String(length=100), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['import_id'], ['product_imports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_products_supplier_id', 'products', ['supplier_id'])
    op.create_index('ix_products_import_id', 'products', ['import_id'])
    op.create_index('ix_products_sku', 'products', ['sku'])
    op.create_index('ix_products_brand', 'products', ['brand'])
    op.create_index('ix_products_category', 'products', ['category'])
    
    # Обновление product_imports
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('product_imports')]
    
    if 'task_id' not in existing_columns:
        op.add_column('product_imports', sa.Column('task_id', sa.String(length=255), nullable=True))
    
    if 'file_format' not in existing_columns:
        op.add_column('product_imports', sa.Column('file_format', sa.String(length=20), nullable=True))
    
    if 'detected_columns' not in existing_columns:
        op.add_column('product_imports', sa.Column('detected_columns', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    if 'generated_tags' not in existing_columns:
        op.add_column('product_imports', sa.Column('generated_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    if 'total_rows' not in existing_columns:
        op.add_column('product_imports', sa.Column('total_rows', sa.Integer(), nullable=True, server_default='0'))
    
    if 'processed_rows' not in existing_columns:
        op.add_column('product_imports', sa.Column('processed_rows', sa.Integer(), nullable=True, server_default='0'))
    
    if 'successful_rows' not in existing_columns:
        op.add_column('product_imports', sa.Column('successful_rows', sa.Integer(), nullable=True, server_default='0'))
    
    if 'failed_rows' not in existing_columns:
        op.add_column('product_imports', sa.Column('failed_rows', sa.Integer(), nullable=True, server_default='0'))
    
    if 'indexed_to_es' not in existing_columns:
        op.add_column('product_imports', sa.Column('indexed_to_es', sa.Integer(), nullable=True, server_default='0'))
    
    if 'es_indexed_count' not in existing_columns:
        op.add_column('product_imports', sa.Column('es_indexed_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('product_imports', 'es_indexed_count')
    op.drop_column('product_imports', 'indexed_to_es')
    op.drop_column('product_imports', 'failed_rows')
    op.drop_column('product_imports', 'successful_rows')
    op.drop_column('product_imports', 'processed_rows')
    op.drop_column('product_imports', 'total_rows')
    op.drop_column('product_imports', 'generated_tags')
    op.drop_column('product_imports', 'detected_columns')
    op.drop_column('product_imports', 'file_format')
    op.drop_column('product_imports', 'task_id')
    
    op.drop_index('ix_products_category', table_name='products')
    op.drop_index('ix_products_brand', table_name='products')
    op.drop_index('ix_products_sku', table_name='products')
    op.drop_index('ix_products_import_id', table_name='products')
    op.drop_index('ix_products_supplier_id', table_name='products')
    
    op.drop_table('products')
