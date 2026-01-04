from app.tasks.celery_app import celery_app
from app.services.pricelist_parser import price_list_parser
from app.core.elasticsearch import es_manager
from app.core.database import db_manager
from app.models.product_import import ProductImport, ImportStatus
from app.models.supplier import Supplier
from app.models.product import Product
import json
from sqlalchemy import select
import logging
import tempfile
import os
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.parsing_tasks.parse_pricelist_task", bind=True)
def parse_pricelist_task(self, supplier_id: str, filename: str, file_content: bytes):
    # ИСПРАВЛЕНИЕ: Получаем или создаём event loop для текущего потока
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def async_parse():
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        import_id = None

        try:
            # Ищем существующую запись
            async for session in db_manager.get_session():
                result = await session.execute(
                    select(ProductImport)
                    .where(
                        ProductImport.supplier_id == supplier_id,
                        ProductImport.file_name == filename,
                        ProductImport.status == "pending"
                    )
                    .order_by(ProductImport.created_at.desc())
                    .limit(1)
                )
                import_record = result.scalar_one_or_none()

                if import_record:
                    import_record.status = ImportStatus.PROCESSING
                    import_record.file_size = len(file_content)
                    import_record.file_format = os.path.splitext(filename)[1]
                    logger.info(f"Using existing import record {import_record.id}")
                else:
                    import_record = ProductImport(
                        supplier_id=supplier_id,
                        file_name=filename,
                        file_size=len(file_content),
                        file_format=os.path.splitext(filename)[1],
                        status=ImportStatus.PROCESSING
                    )
                    session.add(import_record)
                    logger.info(f"Created new import record (fallback)")

                await session.commit()
                import_id = import_record.id
                logger.info(f"Processing import record {import_id} for supplier {supplier_id}")

            # Парсим файл
            parse_result = await price_list_parser.parse_file(tmp_file_path, filename)

            if not parse_result.get("success"):
                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(ProductImport).where(ProductImport.id == import_id)
                    )
                    import_record = result.scalar_one()
                    import_record.status = ImportStatus.FAILED
                    import_record.error_message = parse_result.get("error", "Unknown error")
                    await session.commit()

                return {
                    "status": "failed",
                    "error": parse_result.get("error"),
                    "import_id": str(import_id)
                }

            # Обновляем запись импорта
            async for session in db_manager.get_session():
                result = await session.execute(
                    select(ProductImport).where(ProductImport.id == import_id)
                )
                import_record = result.scalar_one()

                import_record.total_rows = parse_result.get("total_rows", 0)
                import_record.processed_rows = parse_result.get("products_count", 0)
                import_record.successful_rows = parse_result.get("products_count", 0)

                detected_cols = parse_result.get("detected_columns", {})
                import_record.detected_columns = json.loads(
                    json.dumps(detected_cols, default=str).replace(': NaN', ': null')
                )

                tags = parse_result.get("tags", [])
                import_record.generated_tags = [str(t) for t in tags if t and str(t) != 'nan']

                await session.commit()

            # Сохранение товаров
            products_data = parse_result.get("products", [])

            if products_data:
                logger.info(f"Saving {len(products_data)} products to PostgreSQL...")

                async for session in db_manager.get_session():
                    db_products = []
                    for idx, product_data in enumerate(products_data):
                        # Пропускаем товары без SKU (не сохраняем в БД)
                        if not product_data.get("sku"):
                            continue
                        # Пропускаем товары без SKU (не сохраняем в БД)
                        if not product_data.get("sku"):
                            continue
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

                    session.add_all(db_products)
                    await session.commit()
                    logger.info(f"✓ Saved {len(db_products)} products to PostgreSQL")

            # Индексация в Elasticsearch
            products = parse_result.get("products", [])
            if products:
                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(Supplier).where(Supplier.id == supplier_id)
                    )
                    supplier = result.scalar_one()

                    for product in products:
                        product["supplier_id"] = str(supplier_id)
                        product["supplier_name"] = supplier.name
                        product["supplier_inn"] = supplier.inn

                es_result = await es_manager.bulk_index_products(products, supplier_id)

                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(ProductImport).where(ProductImport.id == import_id)
                    )
                    import_record = result.scalar_one()

                    import_record.status = ImportStatus.COMPLETED
                    import_record.indexed_to_es = True
                    import_record.es_indexed_count = es_result.get("success", 0)

                    await session.commit()

                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(Supplier).where(Supplier.id == supplier_id)
                    )
                    supplier = result.scalar_one()
                    # ИСПРАВЛЕНИЕ: Добавляем новые теги к существующим (без дублей)
                    existing_tags = set(supplier.tags_array or [])
                    new_tags = set(parse_result.get("tags", []))
                    supplier.tags_array = list(existing_tags | new_tags)
                    await session.commit()

            logger.info(f"Successfully parsed and indexed {len(products)} products for supplier {supplier_id}")

            return {
                "status": "success",
                "supplier_id": supplier_id,
                "import_id": str(import_id),
                "products_count": len(products),
                "indexed_count": es_result.get("success", 0) if "es_result" in locals() else 0,
                "tags_count": len(parse_result.get("tags", [])),
                "column_mapping": parse_result.get("detected_columns", {})
            }

        except Exception as e:
            logger.error(f"Error parsing pricelist: {e}", exc_info=True)

            if import_id:
                async for session in db_manager.get_session():
                    try:
                        result = await session.execute(
                            select(ProductImport).where(ProductImport.id == import_id)
                        )
                        import_record = result.scalar_one_or_none()
                        if import_record:
                            import_record.status = ImportStatus.FAILED
                            import_record.error_message = str(e)
                            await session.commit()
                    except:
                        pass

            return {
                "status": "failed",
                "error": str(e),
                "import_id": str(import_id) if import_id else None
            }

        finally:
            try:
                os.unlink(tmp_file_path)
            except:
                pass

    # ИСПРАВЛЕНИЕ: Используем существующий loop вместо asyncio.run()
    return loop.run_until_complete(async_parse())
