import anthropic
import json
import re
import logging
from typing import Dict, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIParser:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        
    def parse_supplier_data(self, text: str) -> Optional[Dict]:
        """
        Парсит текст письма/документа и извлекает данные поставщика
        Возвращает словарь с данными для создания поставщика в БД
        """
        system_prompt = """Ты - ассистент по извлечению данных поставщиков из прайс-листов и коммерческих предложений.

Твоя задача: извлечь из текста ВСЮ информацию о поставщике и его товарах.

ВЕРНИ ОТВЕТ СТРОГО В ФОРМАТЕ JSON:
{
  "name": "Название компании (без ООО, ИП и т.д.)",
  "inn": "ИНН (10 или 12 цифр)",
  "kpp": "КПП (9 цифр, если есть)",
  "ogrn": "ОГРН (13-15 цифр, если есть)",
  "email": "Email компании",
  "phone": "Телефон",
  "website": "Сайт (без http://)",
  "legal_address": "Юридический адрес",
  "actual_address": "Фактический адрес",
  "contact_person": "ФИО контактного лица",
  "contact_position": "Должность контактного лица",
  "contact_phone": "Телефон контактного лица",
  "contact_email": "Email контактного лица",
  "payment_terms": "Условия оплаты",
  "min_order_sum": "Минимальная сумма заказа (число)",
  "delivery_regions": ["Регион 1", "Регион 2"],
  "tags": ["бренд1", "бренд2", "категория1"],
  "notes": "Дополнительная информация"
}

ПРАВИЛА:
1. Если поле не найдено - используй null
2. ИНН ОБЯЗАТЕЛЕН - без него верни {"error": "ИНН не найден"}
3. Теги - это бренды, производители, категории товаров (нормализуй: строчные буквы, без кавычек, без ООО/ИП)
4. Название компании очисти от ООО, ИП, ЗАО и т.д.
5. Телефоны и email очисти от лишних символов
6. min_order_sum - только число без валюты
7. Не добавляй комментарии, только JSON"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Извлеки данные поставщика из текста:\n\n{text[:10000]}"}
                ]
            )
            
            response_text = message.content[0].text
            logger.info(f"Claude response: {response_text[:200]}")
            
            # Парсим JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                
                # Проверяем обязательные поля
                if data.get('error'):
                    logger.error(f"AI Parser error: {data['error']}")
                    return None
                    
                if not data.get('inn'):
                    logger.error("ИНН не найден в ответе AI")
                    return None
                
                # Нормализуем теги
                if data.get('tags'):
                    data['tags'] = self.normalize_tags(data['tags'])
                
                return data
            else:
                logger.error("Не удалось найти JSON в ответе Claude")
                return None
                
        except Exception as e:
            logger.error(f"AI parsing error: {str(e)}")
            return None
    
    def normalize_tags(self, tags: List[str]) -> List[str]:
        """Нормализация тегов"""
        normalized = []
        for tag in tags:
            # Приводим к нижнему регистру
            tag = tag.lower().strip()
            # Убираем кавычки
            tag = tag.replace('"', '').replace("'", '')
            # Убираем ООО, ИП и т.д.
            tag = re.sub(r'\b(ооо|ип|зао|оао|пао|ао)\b', '', tag).strip()
            # Убираем лишние пробелы
            tag = re.sub(r'\s+', ' ', tag)
            
            if tag and len(tag) > 1:
                normalized.append(tag)
        
        return list(set(normalized))  # Убираем дубликаты

ai_parser = AIParser()
