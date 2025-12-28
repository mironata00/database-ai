#!/bin/bash
# ФИНАЛЬНЫЙ ПАТЧ ДЛЯ ПАРСИНГА ПРАЙС-ЛИСТОВ
# Database AI v2
# Дата: 2025-12-28

set -e

echo "========================================="
echo "DATABASE AI - ПАРСИНГ ПРАЙС-ЛИСТОВ"
echo "Применение патча..."
echo "========================================="

cd /root/database-ai

# ============================================
# ШАГ 1: Создание модели Product
# ============================================
echo ""
echo "ШАГ 1: Создание модели Product..."

cat > back/app/models/product.py << 'EOF'
"""
Модель Product - товары из прайс-листов
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    """Товары из прайс-листов поставщиков"""
    __tablename__ = "products"
    __table_args__ = (
        Index('idx_product_text_search', 'name', 'sku', postgresql_using='gin'),
        {'extend_existing': True}
    )
    
    # Foreign keys
    supplier_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("suppliers.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Основные поля
    sku = Column(String(255), index=True)
    name = Column(Text, nullable=False)
    brand = Column(String(255), index=True)
    category = Column(String(255), index=True)
    
    # Цена и остатки
    price = Column(Float)
    old_price = Column(Float)
    unit = Column(String(50))
    stock = Column(Integer)
    min_order = Column(Float)
    
    # Дополнительно
    description = Column(Text)
    specifications = Column(JSON)
    barcode = Column(String(100))
    vendor_code = Column(String(100))
    raw_text = Column(Text)
    row_number = Column(Integer)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    product_import = relationship("ProductImport", back_populates="products")
    
    def __repr__(self):
        return f"<Product {self.sku}: {self.name[:50]}>"
EOF

echo "✓ Создан back/app/models/product.py"

# ============================================
# ШАГ 2: Обновление models/__init__.py
# ============================================
echo ""
echo "ШАГ 2: Обновление models/__init__.py..."

cat > back/app/models/__init__.py << 'EOF'
from app.models.base import Base, BaseModel
from app.models.user import User, UserRole
from app.models.supplier import Supplier, SupplierStatus
from app.models.rating import Rating
from app.models.email import (
    EmailTemplate,
    EmailCampaign,
    CampaignRecipient,
    EmailThread,
    EmailDirection,
    CampaignStatus,
)
from app.models.product_import import ProductImport, ImportStatus
from app.models.product import Product  # ДОБАВЛЕНО
from app.models.audit_log import AuditLog, AuditAction

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "Supplier",
    "SupplierStatus",
    "Rating",
    "EmailTemplate",
    "EmailCampaign",
    "CampaignRecipient",
    "EmailThread",
    "EmailDirection",
    "CampaignStatus",
    "ProductImport",
    "ImportStatus",
    "Product",  # ДОБАВЛЕНО
    "AuditLog",
    "AuditAction",
]
EOF

echo "✓ Обновлен back/app/models/__init__.py"

# ============================================
# ШАГ 3: Обновление ProductImport
# ============================================
echo ""
echo "ШАГ 3: Обновление модели ProductImport..."

cat > back/app/models/product_import.py << 'EOF'
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductImport(BaseModel):
    __tablename__ = "product_imports"
    __table_args__ = {'extend_existing': True}

    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Файл
    file_url = Column(String(1000))
    file_name = Column(String(500))
    file_size = Column(Integer)
    file_format = Column(String(20))
    
    # Статус
    status = Column(String(50), default='pending', index=True)
    total_products = Column(Integer, default=0)
    parsed_products = Column(Integer, default=0)
    error_message = Column(Text)
    completed_at = Column(DateTime)
    
    # НОВЫЕ ПОЛЯ
    task_id = Column(String(255))
    detected_columns = Column(JSON)
    generated_tags = Column(JSON)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    indexed_to_es = Column(Integer, default=0)
    es_indexed_count = Column(Integer, default=0)

    # Relationships
    supplier = relationship("Supplier", back_populates="product_imports")
    products = relationship(
        "Product", 
        back_populates="product_import",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<ProductImport {self.file_name} ({self.status})>"
    
    def get_progress_percent(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)
EOF

echo "✓ Обновлен back/app/models/product_import.py"

# ============================================
# ШАГ 4: Обновление Supplier (relationship)
# ============================================
echo ""
echo "ШАГ 4: Добавление relationship в Supplier..."

# Проверяем есть ли уже relationship к products
if ! grep -q "products = relationship" back/app/models/supplier.py; then
    # Добавляем перед последней строкой (обычно __repr__)
    sed -i '/def __repr__/i\    # Relationship to products\n    products = relationship(\n        "Product",\n        back_populates="supplier",\n        cascade="all, delete-orphan",\n        lazy="dynamic"\n    )\n' back/app/models/supplier.py
    echo "✓ Добавлен relationship к Product в Supplier"
else
    echo "⚠ Relationship к Product уже существует в Supplier"
fi

# ============================================
# ШАГ 5: ГЛАВНОЕ - Обновление эндпоинта
# ============================================
echo ""
echo "ШАГ 5: Исправление эндпоинта upload-pricelist-new..."

# Создаём временный файл с новым эндпоинтом
cat > /tmp/new_endpoint.py << 'EOF'

@router.post("/{supplier_id}/upload-pricelist-new")
async def upload_pricelist_new(
    supplier_id: UUID, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """Загрузить прайс-лист и запустить парсинг"""
    from app.models.product_import import ProductImport
    from app.tasks.parsing_tasks import parse_pricelist_task  # ДОБАВЛЕНО
    import os
    from datetime import datetime

    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Создать директорию по ИНН
    upload_dir = f"/app/uploads/{supplier.inn}"
    os.makedirs(upload_dir, exist_ok=True)

    # Сохранить файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Создать запись в БД
    import_record = ProductImport(
        supplier_id=supplier_id,
        file_name=file.filename,
        file_url=filepath,
        file_size=len(content),
        status="pending",
        total_products=0,
        parsed_products=0
    )

    db.add(import_record)
    await db.commit()
    await db.refresh(import_record)

    # ============================================
    # ГЛАВНОЕ ИСПРАВЛЕНИЕ: Запускаем Celery task!
    # ============================================
    try:
        task = parse_pricelist_task.delay(
            str(supplier_id),
            file.filename,
            content
        )
        
        import_record.status = "processing"
        import_record.task_id = task.id
        await db.commit()
        
        return {
            "import_id": str(import_record.id),
            "task_id": task.id,
            "status": "processing",
            "file_url": filepath,
            "message": "File uploaded and parsing started"
        }
        
    except Exception as e:
        import_record.status = "failed"
        import_record.error_message = f"Failed to start parsing: {str(e)}"
        await db.commit()
        
        raise HTTPException(
            status_code=500, 
            detail=f"File uploaded but parsing failed: {str(e)}"
        )
EOF

# Заменяем старый эндпоинт на новый
python3 << 'PYTHON_SCRIPT'
import re

# Читаем файл
with open('back/app/api/suppliers.py', 'r') as f:
    content = f.read()

# Ищем старый эндпоинт upload-pricelist-new
pattern = r'@router\.post\("\{supplier_id\}/upload-pricelist-new"\).*?(?=@router\.|$)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Читаем новый эндпоинт
    with open('/tmp/new_endpoint.py', 'r') as f:
        new_endpoint = f.read()
    
    # Заменяем
    content = content[:match.start()] + new_endpoint.strip() + '\n\n' + content[match.end():]
    
    # Добавляем импорт parse_pricelist_task если его нет
    if 'from app.tasks.parsing_tasks import parse_pricelist_task' not in content:
        # Находим блок импортов
        import_block = re.search(r'(from app\.models\..*?import.*?\n)+', content)
        if import_block:
            insert_pos = import_block.end()
            content = content[:insert_pos] + 'from app.tasks.parsing_tasks import parse_pricelist_task\n' + content[insert_pos:]
    
    # Сохраняем
    with open('back/app/api/suppliers.py', 'w') as f:
        f.write(content)
    
    print("✓ Эндпоинт upload-pricelist-new обновлён")
else:
    print("⚠ Эндпоинт upload-pricelist-new не найден")
PYTHON_SCRIPT

# ============================================
# ШАГ 6: Обновление parsing_tasks.py
# ============================================
echo ""
echo "ШАГ 6: Обновление parsing_tasks.py для сохранения в БД..."

# Добавляем импорт Product если его нет
if ! grep -q "from app.models.product import Product" back/app/tasks/parsing_tasks.py; then
    sed -i '/from app.models.supplier import Supplier/a from app.models.product import Product' back/app/tasks/parsing_tasks.py
    echo "✓ Добавлен импорт Product"
fi

# Заменяем секцию сохранения в БД
python3 << 'PYTHON_SCRIPT'
import re

with open('back/app/tasks/parsing_tasks.py', 'r') as f:
    content = f.read()

# Ищем блок после "Обновляем запись импорта" и до "# Индексируем в Elasticsearch"
old_section = re.search(
    r'(# Обновляем запись импорта.*?await session\.commit\(\))\s*(# Индексируем в Elasticsearch)',
    content,
    re.DOTALL
)

if old_section:
    new_section = '''# Обновляем запись импорта
            async for session in db_manager.get_session():
                result = await session.execute(
                    select(ProductImport).where(ProductImport.id == import_id)
                )
                import_record = result.scalar_one()

                import_record.total_rows = parse_result.get("total_rows", 0)
                import_record.processed_rows = parse_result.get("products_count", 0)
                import_record.successful_rows = parse_result.get("products_count", 0)
                import_record.detected_columns = parse_result.get("detected_columns", {})
                import_record.generated_tags = parse_result.get("tags", [])

                await session.commit()

            # ============================================
            # СОХРАНЕНИЕ ТОВАРОВ В PostgreSQL
            # ============================================
            products_data = parse_result.get("products", [])
            
            if products_data:
                logger.info(f"Saving {len(products_data)} products to PostgreSQL...")
                
                async for session in db_manager.get_session():
                    # Создаём объекты Product
                    db_products = []
                    for idx, product_data in enumerate(products_data):
                        product = Product(
                            supplier_id=supplier_id,
                            import_id=import_id,
                            sku=product_data.get("sku"),
                            name=product_data.get("name"),
                            brand=product_data.get("brand"),
                            category=product_data.get("category"),
                            price=product_data.get("price"),
                            unit=product_data.get("unit"),
                            stock=product_data.get("stock"),
                            raw_text=product_data.get("raw_text"),
                            row_number=idx + 1
                        )
                        db_products.append(product)
                    
                    # Bulk insert
                    session.add_all(db_products)
                    await session.commit()
                    
                    logger.info(f"✓ Saved {len(db_products)} products to PostgreSQL")

            '''
    
    content = content[:old_section.start()] + new_section + '\n            ' + old_section.group(2) + content[old_section.end():]
    
    with open('back/app/tasks/parsing_tasks.py', 'w') as f:
        f.write(content)
    
    print("✓ Обновлён parsing_tasks.py")
else:
    print("⚠ Не удалось найти блок для замены в parsing_tasks.py")
PYTHON_SCRIPT

echo ""
echo "========================================="
echo "Патч применён успешно!"
echo "========================================="
echo ""
echo "СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Создать миграцию БД:"
echo "   docker compose exec api alembic revision -m 'add products table'"
echo ""
echo "2. Отредактировать миграцию (добавить код из alembic_migration.txt)"
echo ""
echo "3. Применить миграцию:"
echo "   docker compose exec api alembic upgrade head"
echo ""
echo "4. Перезапустить сервисы:"
echo "   docker compose restart api celery_worker_parsing"
echo ""
echo "5. Проверить логи:"
echo "   docker compose logs celery_worker_parsing -f"
echo ""
echo "========================================="
