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

    async def parse_file(self, file_path: str, filename: str) -> Dict:
        """Парсит файл прайс-листа."""
        logger.info(f"Parsing file: {filename}")

        file_ext = Path(filename).suffix.lower()

        try:
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
                return {"success": False, "error": "No data found in file"}

            logger.info(f"Loaded DataFrame: {len(df)} rows, {len(df.columns)} columns")

            detected_columns = column_detector.detect_columns(df)

            if not detected_columns:
                return {
                    "success": False,
                    "error": "Could not detect any columns",
                    "columns_found": list(df.columns)
                }

            required = settings.PARSING_REQUIRED_COLUMNS_LIST
            missing = [col for col in required if col not in detected_columns]

            if missing:
                logger.warning(f"Missing required columns: {missing}")
                logger.info(f"Continuing with detected columns: {list(detected_columns.keys())}")

            df_renamed = df.rename(columns={
                detected_columns.get(col_type): col_type
                for col_type in detected_columns
            })

            products = self._extract_products(df_renamed, detected_columns)
            tags = self._generate_tags(products)
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
            return {"success": False, "error": str(e)}

    async def _parse_excel(self, file_path: str) -> pd.DataFrame:
        """Парсит Excel файл БЕЗ предустановленных заголовков."""
        df = pd.read_excel(file_path, header=None, nrows=self.max_rows)
        df = df.dropna(how='all')
        header_row = self._find_header_row(df)
        df.columns = df.iloc[header_row].values
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        return df

    async def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """Парсит CSV файл."""
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
        """Парсит PDF файл с таблицами."""
        all_tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:10]:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if len(table) > 1:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_tables.append(df)

        if all_tables:
            df = pd.concat(all_tables, ignore_index=True)
            return df
        return pd.DataFrame()

    async def _parse_txt(self, file_path: str) -> pd.DataFrame:
        """Парсит TXT файл."""
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
            df = pd.read_csv(
                file_path,
                delim_whitespace=True,
                encoding=self.default_encoding,
                nrows=self.max_rows,
                on_bad_lines='skip'
            )
            return df.dropna(how='all')

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Умно находит строку с заголовками."""
        import re

        header_keywords = [
            'артикул', 'sku', 'код', 'article',
            'наименование', 'название', 'name', 'товар',
            'цена', 'price', 'стоимость', 'ррц',
            'бренд', 'brand', 'производитель',
            'категория', 'category', 'группа',
            'единица', 'unit', 'ед',
            'остаток', 'stock', 'наличие', 'количество'
        ]

        best_row = 0
        best_score = 0

        for i in range(min(30, len(df))):
            row = df.iloc[i]
            score = 0
            row_values = [str(v).lower().strip() for v in row if not pd.isna(v)]

            if len(row_values) == 0:
                continue

            fill_pct = len(row_values) / len(row)
            if fill_pct < 0.3:
                continue
            score += fill_pct * 10

            keyword_matches = 0
            for val in row_values:
                val_clean = re.sub(r'[^\w\s]', '', val, flags=re.UNICODE)
                for keyword in header_keywords:
                    if keyword in val_clean:
                        keyword_matches += 1
                        break

            if keyword_matches > 0:
                score += keyword_matches * 20

            avg_len = sum(len(v) for v in row_values) / len(row_values)
            if 5 < avg_len < 30:
                score += 10
            elif avg_len > 50:
                score -= 20

            numeric_count = 0
            for val in row_values:
                try:
                    float(val.replace(',', '.').replace(' ', ''))
                    numeric_count += 1
                except:
                    pass

            if numeric_count / len(row_values) < 0.3:
                score += 15
            else:
                score -= 10

            if score > best_score:
                best_score = score
                best_row = i

        logger.info(f"Header detection: found row {best_row} with score {best_score}")
        logger.info(f"First row values: {df.iloc[0].tolist()[:5]}")
        if best_row > 0:
            logger.info(f"Selected header row {best_row} values: {df.iloc[best_row].tolist()[:5]}")

        return best_row

    def _normalize_text(self, text: str) -> str:
        """Нормализует текст товара."""
        import re

        if not text or pd.isna(text):
            return ""

        text = str(text)
        text = text.replace(',', '')
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _extract_products(self, df: pd.DataFrame, detected_columns: Dict[str, str]) -> List[Dict]:
        """Извлекает товары из DataFrame."""
        products = []

        for idx, row in df.iterrows():
            try:
                product = {}

                if 'sku' in detected_columns:
                    sku = row.get('sku')
                    if pd.isna(sku) or str(sku).strip() == '':
                        continue
                    product['sku'] = str(sku).strip()

                if 'name' in detected_columns:
                    name = row.get('name')
                    if pd.isna(name) or str(name).strip() == '' or str(name).lower() == 'nan':
                        continue
                    product['name'] = self._normalize_text(name)
                else:
                    continue

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

                product['raw_text'] = ' '.join([
                    str(v) for v in row.values if not pd.isna(v) and str(v).lower() != 'nan'
                ])

                products.append(product)

            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue

        logger.info(f"Extracted {len(products)} products")
        return products

    def _generate_tags(self, products: List[Dict]) -> List[str]:
        """Генерирует уникальные теги из товаров."""
        tags = set()

        for product in products:
            # НОВОЕ: Добавляем SKU (артикулы/коды) в теги
            if 'sku' in product and product['sku']:
                tags.add(product['sku'].strip())

            if 'brand' in product and product['brand']:
                tags.add(product['brand'])

            if 'category' in product and product['category']:
                tags.add(product['category'])

            if 'name' in product and product['name']:
                words = product['name'].lower().split()
                for word in words:
                    if len(word) > 3 and not word.isdigit():
                        tags.add(word)

        tags = sorted(list(tags))

        logger.info(f"Generated {len(tags)} unique tags")
        return tags


price_list_parser = PriceListParser()
