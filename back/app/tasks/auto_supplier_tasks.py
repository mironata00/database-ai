from celery import shared_task
from app.utils.imap_client import imap_client
from app.utils.text_extractor import text_extractor
from app.utils.ai_parser import ai_parser
from app.core.config import settings
from app.models.supplier import Supplier
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Создаем синхронную сессию для Celery
sync_engine = create_engine(
    settings.DATABASE_URL.replace('postgresql+asyncpg', 'postgresql+psycopg2'),
    pool_pre_ping=True
)
SyncSession = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@shared_task
def process_supplier_emails():
    """
    Автоматическая обработка писем с прайс-листами:
    1. Получаем непрочитанные письма из IMAP
    2. Извлекаем текст из тела письма и вложений  
    3. Отправляем в Claude AI для парсинга
    4. Создаем поставщика в БД
    """
    logger.info("Starting automatic supplier email processing")
    
    try:
        # Получаем непрочитанные письма
        messages = imap_client.get_unread_messages()
        logger.info(f"Found {len(messages)} unread messages")
        
        processed = 0
        created = 0
        errors = 0
        
        for msg in messages:
            try:
                logger.info(f"Processing email: {msg['subject']} from {msg['sender']}")
                
                # Собираем весь текст
                full_text = f"Тема: {msg['subject']}\nОт: {msg['sender']}\n\n{msg['body']}\n\n"
                
                # Извлекаем текст из вложений
                for attachment in msg['attachments']:
                    filename = attachment['filename']
                    file_data = attachment['data']
                    
                    logger.info(f"Extracting text from: {filename}")
                    extracted_text = text_extractor.extract_text(file_data, filename)
                    
                    if extracted_text:
                        full_text += f"\n[{filename}]:\n{extracted_text}\n"
                
                # AI парсинг
                logger.info("Sending to Claude AI...")
                supplier_data = ai_parser.parse_supplier_data(full_text)
                
                if not supplier_data:
                    logger.warning(f"AI parsing failed for {msg['id']}")
                    errors += 1
                    continue
                
                # Работа с БД
                db = SyncSession()
                try:
                    # Проверяем дубликат по ИНН
                    result = db.execute(select(Supplier).where(Supplier.inn == supplier_data['inn']))
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        logger.info(f"Supplier INN {supplier_data['inn']} exists, skipping")
                        processed += 1
                    else:
                        # Создаем нового
                        new_supplier = Supplier(
                            name=supplier_data.get('name'),
                            inn=supplier_data.get('inn'),
                            kpp=supplier_data.get('kpp'),
                            ogrn=supplier_data.get('ogrn'),
                            email=supplier_data.get('email'),
                            phone=supplier_data.get('phone'),
                            website=supplier_data.get('website'),
                            legal_address=supplier_data.get('legal_address'),
                            actual_address=supplier_data.get('actual_address'),
                            contact_person=supplier_data.get('contact_person'),
                            contact_position=supplier_data.get('contact_position'),
                            contact_phone=supplier_data.get('contact_phone'),
                            contact_email=supplier_data.get('contact_email'),
                            payment_terms=supplier_data.get('payment_terms'),
                            min_order_sum=supplier_data.get('min_order_sum'),
                            delivery_regions=supplier_data.get('delivery_regions', []),
                            tags_array=supplier_data.get('tags', []),
                            notes=supplier_data.get('notes'),
                            status='PENDING',
                            color='#6B7280'
                        )
                        
                        db.add(new_supplier)
                        db.commit()
                        db.refresh(new_supplier)
                        
                        logger.info(f"Created: {new_supplier.name} (INN: {new_supplier.inn})")
                        created += 1
                    
                finally:
                    db.close()
                
                # Помечаем прочитанным
                imap_client.mark_as_read(msg['id'])
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing {msg.get('id')}: {e}")
                errors += 1
        
        result = {'processed': processed, 'created': created, 'errors': errors}
        logger.info(f"Completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return {'processed': 0, 'created': 0, 'errors': 1, 'error': str(e)}
