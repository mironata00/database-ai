"""
Price List Parser Service
Парсинг прайс-листов с автоматическим определением колонок
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io
import logging
from pathlib import Path

from app.core.config import settings
from app.services.column_detector import column_detector

logger = logging.getLogger(__name__)


class PriceListParser:
    """Парсер прайс-листов с поддержкой различных форматов."""
    
    def __init__(self):
        self.max_rows = settings.PARSING_MAX_ROWS_PER_FILE
        self.auto_detect_encoding = settings.PARSING_AUTO_DETECT_ENCODING
        self.default_encoding = settings.PARSING_DEFAULT_ENCODING
    
    async def parse_file(
        self, 
        file_path: str,
        filename: str
    ) -> Dict:
        """
        Парсит файл прайс-листа.
        
        Args:
            file_path: Путь к файлу
            filename: Имя файла
            
        Returns:
            Dict с результатами парсинга
        """
        logger.info(f"Parsing file: {filename}")
        
        # Определяем формат
        file_ext = Path(filename).suffix.lower()
        
        try:
            # Читаем файл в DataFrame
            if file_ext in ['.xlsx', '.xls']:
                df = await self._parse_excel(file_path)
            elif file_ext == '.csv':
                df = await self._parse_csv(file_path)
            elif file_ext == '.pdf':
                df = await self._parse_pdf(file_path)
            elif file_ext == '.txt':
                df = await self._parse_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            if df is None or df.empty:
                return {
                    "success": False,
                    "error": "No data found in file"
                }
            
            logger.info(f"Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")
            
            # Детектируем колонки
            detected_columns = column_detector.detect_columns(df)
            
            if not detected_columns:
                return {
                    "success": False,
                    "error": "Could not detect any columns",
                    "columns_found": list(df.columns)
                }
            
            # Проверяем обязательные колонки
            required = settings.PARSING_REQUIRED_COLUMNS_LIST
            missing = [col for col in required if col not in detected_columns]
            
            if missing:
                logger.warning(f"Missing required columns: {missing}")
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing)}",
                    "detected_columns": detected_columns,
                    "columns_found": list(df.columns)
                }
            
            # Переименовываем колонки
            df_renamed = df.rename(columns={
                detected_columns.get(col_type): col_type 
                for col_type in detected_columns
            })
            
            # Парсим данные
            products = self._extract_products(df_renamed, detected_columns)
            
            # Генерируем теги
            tags = self._generate_tags(products)
            
            # Отчет
            report = column_detector.get_mapping_report(detected_columns)
            logger.info(f"\n{report}")
            
            return {
                "success": True,
                "total_rows": len(df),
                "detected_columns": detected_columns,
                "products_count": len(products),
                "products": products,
                "tags": tags,
                "column_mapping_report": report
            }
            
        except Exception as e:
            logger.error(f"Error parsing file: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _parse_excel(self, file_path: str) -> pd.DataFrame:
        """Парсит Excel файл."""
        # Читаем первый лист (можно расширить на все листы)
        df = pd.read_excel(file_path, nrows=self.max_rows)
        
        # Убираем полностью пустые строки
        df = df.dropna(how='all')
        
        # Определяем строку с заголовками (первая строка с >50% заполненных ячеек)
        header_row = self._find_header_row(df)
        
        if header_row > 0:
            # Устанавливаем правильную строку заголовков
            df.columns = df.iloc[header_row].values
            df = df.iloc[header_row + 1:].reset_index(drop=True)
        
        return df
    
    async def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """Парсит CSV файл."""
        # Определяем разделитель
        with open(file_path, 'r', encoding=self.default_encoding, errors='ignore') as f:
            first_line = f.readline()
            delimiter = ',' if ',' in first_line else ';' if ';' in first_line else '\t'
        
        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=self.default_encoding,
            nrows=self.max_rows,
            on_bad_lines='skip'
        )
        
        return df.dropna(how='all')
    
    async def _parse_pdf(self, file_path: str) -> pd.DataFrame:
        """Парсит PDF файл."""
        all_tables = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:10]:  # Первые 10 страниц
                # Пытаемся извлечь таблицы
                tables = page.extract_tables()
                
                if tables:
                    for table in tables:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        all_tables.append(df)
                
                # Если таблиц нет и включен OCR
                elif settings.PARSING_PDF_USE_OCR:
                    # OCR fallback (медленно, использовать осторожно)
                    pass
        
        if all_tables:
            df = pd.concat(all_tables, ignore_index=True)
            return df
        
        return pd.DataFrame()
    
    async def _parse_txt(self, file_path: str) -> pd.DataFrame:
        """Парсит TXT файл (tab/space delimited)."""
        try:
            df = pd.read_csv(
                file_path,
                delimiter='\t',
                encoding=self.default_encoding,
                nrows=self.max_rows,
                on_bad_lines='skip'
            )
            return df.dropna(how='all')
        except:
            # Fallback to space delimiter
            df = pd.read_csv(
                file_path,
                delim_whitespace=True,
                encoding=self.default_encoding,
                nrows=self.max_rows,
                on_bad_lines='skip'
            )
            return df.dropna(how='all')
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """
        Находит строку с заголовками.
        
        Args:
            df: DataFrame
            
        Returns:
            Индекс строки с заголовками
        """
        for i in range(min(10, len(df))):  # Проверяем первые 10 строк
            row = df.iloc[i]
            non_null_pct = row.notna().sum() / len(row)
            
            # Если >50% ячеек заполнены и это текст
            if non_null_pct > 0.5:
                text_pct = row.astype(str).str.len().gt(0).sum() / len(row)
                if text_pct > 0.5:
                    return i
        
        return 0
    
    def _extract_products(
        self, 
        df: pd.DataFrame, 
        detected_columns: Dict[str, str]
    ) -> List[Dict]:
        """
        Извлекает товары из DataFrame.
        
        Args:
            df: DataFrame с переименованными колонками
            detected_columns: Маппинг определенных колонок
            
        Returns:
            Список словарей с товарами
        """
        products = []
        
        for idx, row in df.iterrows():
            try:
                product = {}
                
                # Обязательные поля
                if 'sku' in detected_columns:
                    sku = row.get('sku')
                    if pd.isna(sku) or str(sku).strip() == '':
                        continue
                    product['sku'] = str(sku).strip()
                
                if 'name' in detected_columns:
                    name = row.get('name')
                    if pd.isna(name):
                        continue
                    product['name'] = str(name).strip()
                
                if 'price' in detected_columns:
                    price = row.get('price')
                    try:
                        # Убираем валюту и парсим число
                        price_str = str(price).replace('₽', '').replace('руб', '').replace(' ', '').replace(',', '.')
                        product['price'] = float(price_str)
                    except:
                        product['price'] = 0.0
                
                # Опциональные поля
                if 'brand' in detected_columns:
                    brand = row.get('brand')
                    if not pd.isna(brand):
                        product['brand'] = str(brand).strip().lower()
                
                if 'category' in detected_columns:
                    category = row.get('category')
                    if not pd.isna(category):
                        product['category'] = str(category).strip().lower()
                
                if 'unit' in detected_columns:
                    unit = row.get('unit')
                    if not pd.isna(unit):
                        product['unit'] = str(unit).strip()
                
                if 'stock' in detected_columns:
                    stock = row.get('stock')
                    try:
                        product['stock'] = int(float(stock))
                    except:
                        pass
                
                # Полный текст для Elasticsearch
                product['raw_text'] = ' '.join([
                    str(v) for v in row.values if not pd.isna(v)
                ])
                
                products.append(product)
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue
        
        logger.info(f"Extracted {len(products)} products")
        return products
    
    def _generate_tags(self, products: List[Dict]) -> List[str]:
        """
        Генерирует уникальные теги из товаров.
        
        Args:
            products: Список товаров
            
        Returns:
            Список уникальных тегов
        """
        tags = set()
        
        for product in products:
            # Добавляем бренды
            if 'brand' in product:
                tags.add(product['brand'])
            
            # Добавляем категории
            if 'category' in product:
                tags.add(product['category'])
            
            # Извлекаем ключевые слова из наименования
            if 'name' in product:
                words = product['name'].lower().split()
                # Добавляем слова длиннее 3 символов
                for word in words:
                    if len(word) > 3:
                        tags.add(word)
        
        # Ограничиваем количество тегов
        tags = sorted(list(tags))[:settings.PARSING_MAX_TAGS_PER_SUPPLIER]
        
        logger.info(f"Generated {len(tags)} unique tags")
        return tags


# Singleton instance
price_list_parser = PriceListParser()
