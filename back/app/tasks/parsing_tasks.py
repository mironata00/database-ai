from app.tasks.celery_app import celery_app
from app.services.price_list_parser import price_list_parser
from app.core.elasticsearch import es_manager
from app.core.database import db_manager
from app.models.product_import import ProductImport, ImportStatus
from app.models.supplier import Supplier
from sqlalchemy import select
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.parsing_tasks.parse_pricelist_task", bind=True)
def parse_pricelist_task(self, supplier_id: str, filename: str, file_content: bytes):
    """
    Парсит прайс-лист и индексирует в Elasticsearch.
    
    Args:
        supplier_id: ID поставщика
        filename: Название файла
        file_content: Содержимое файла в байтах
    """
    import asyncio
    
    async def async_parse():
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Создаем запись импорта
            async for session in db_manager.get_session():
                import_record = ProductImport(
                    supplier_id=supplier_id,
                    source_type="manual_upload",
                    filename=filename,
                    file_size=len(file_content),
                    file_format=os.path.splitext(filename)[1],
                    status=ImportStatus.PROCESSING
                )
                session.add(import_record)
                await session.commit()
                import_id = import_record.id
                
                logger.info(f"Created import record {import_id} for supplier {supplier_id}")
            
            # Парсим файл
            parse_result = await price_list_parser.parse_file(tmp_file_path, filename)
            
            if not parse_result.get("success"):
                # Обновляем статус на failed
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
                import_record.detected_columns = parse_result.get("detected_columns", {})
                import_record.generated_tags = parse_result.get("tags", [])
                
                await session.commit()
            
            # Индексируем в Elasticsearch
            products = parse_result.get("products", [])
            if products:
                # Добавляем supplier_id к каждому товару
                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(Supplier).where(Supplier.id == supplier_id)
                    )
                    supplier = result.scalar_one()
                    
                    for product in products:
                        product["supplier_id"] = str(supplier_id)
                        product["supplier_name"] = supplier.name
                        product["supplier_inn"] = supplier.inn
                
                # Bulk индексация
                es_result = await es_manager.bulk_index_products(products, supplier_id)
                
                # Обновляем статус
                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(ProductImport).where(ProductImport.id == import_id)
                    )
                    import_record = result.scalar_one()
                    
                    import_record.status = ImportStatus.COMPLETED
                    import_record.indexed_to_es = True
                    import_record.es_indexed_count = es_result.get("success", 0)
                    
                    await session.commit()
                
                # Обновляем теги у поставщика
                async for session in db_manager.get_session():
                    result = await session.execute(
                        select(Supplier).where(Supplier.id == supplier_id)
                    )
                    supplier = result.scalar_one()
                    supplier.tags_array = parse_result.get("tags", [])
                    await session.commit()
            
            logger.info(f"Successfully parsed and indexed {len(products)} products for supplier {supplier_id}")
            
            return {
                "status": "success",
                "supplier_id": supplier_id,
                "import_id": str(import_id),
                "products_count": len(products),
                "indexed_count": es_result.get("success", 0),
                "tags_count": len(parse_result.get("tags", [])),
                "column_mapping": parse_result.get("detected_columns", {})
            }
            
        except Exception as e:
            logger.error(f"Error parsing pricelist: {e}", exc_info=True)
            
            # Обновляем статус на failed
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
                "error": str(e)
            }
        
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_file_path)
            except:
                pass
    
    # Запускаем async функцию
    return asyncio.run(async_parse())
