"""
Price List Parser Service
Парсинг прайс-листов с автоматическим определением колонок
Поддержка ВСЕХ листов Excel файла
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import pdfplumber
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
        logger.info(f"========================================")
        logger.info(f"Parsing file: {filename}")
        logger.info(f"========================================")

        file_ext = Path(filename).suffix.lower()

        try:
            if file_ext in ['.xlsx', '.xls']:
                result = await self._parse_excel_all_sheets(file_path)
            elif file_ext == '.csv':
                df = await self._parse_csv(file_path)
                result = {'dataframes': [{'sheet': 'CSV', 'df': df}]} if df is not None and not df.empty else None
            elif file_ext == '.pdf':
                df = await self._parse_pdf(file_path)
                result = {'dataframes': [{'sheet': 'PDF', 'df': df}]} if df is not None and not df.empty else None
            elif file_ext == '.txt':
                df = await self._parse_txt(file_path)
                result = {'dataframes': [{'sheet': 'TXT', 'df': df}]} if df is not None and not df.empty else None
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            if result is None or not result.get('dataframes'):
                return {"success": False, "error": "No data found in file"}

            all_products = []
            all_tags = set()
            total_rows = 0
            sheets_info = []
            
            total_sku_tags = 0
            total_brand_tags = 0
            total_category_tags = 0
            total_word_tags = 0

            for sheet_data in result['dataframes']:
                sheet_name = sheet_data['sheet']
                df = sheet_data['df']
                
                if df is None or df.empty:
                    continue

                logger.info(f"")
                logger.info(f"========================================")
                logger.info(f"Processing sheet '{sheet_name}'")
                logger.info(f"Rows: {len(df)}, Columns: {len(df.columns)}")
                logger.info(f"========================================")
                total_rows += len(df)

                detected_columns = column_detector.detect_columns(df)

                if not detected_columns:
                    logger.warning(f"Sheet '{sheet_name}': Could not detect columns, skipping")
                    sheets_info.append({
                        'name': sheet_name,
                        'rows': len(df),
                        'status': 'skipped',
                        'reason': 'No columns detected'
                    })
                    continue

                df_renamed = df.rename(columns={
                    detected_columns.get(col_type): col_type
                    for col_type in detected_columns
                    if detected_columns.get(col_type) is not None
                })

                products = self._extract_products(df_renamed, detected_columns, sheet_name)
                
                products_with_sku = sum(1 for p in products if p.get('sku'))
                products_without_sku = len(products) - products_with_sku
                
                logger.info(f"")
                logger.info(f"=== PRODUCT EXTRACTION STATS ===")
                logger.info(f"Total products extracted: {len(products)}")
                logger.info(f"Products WITH SKU: {products_with_sku}")
                logger.info(f"Products WITHOUT SKU: {products_without_sku}")
                
                sheet_tags = set()
                sheet_sku_tags = 0
                sheet_brand_tags = 0
                sheet_category_tags = 0
                sheet_word_tags = 0
                
                for product in products:
                    if product.get('sku'):
                        sku = product['sku'].strip()
                        sheet_tags.add(sku)
                        sheet_sku_tags += 1
                    
                    if product.get('brand'):
                        brand = product['brand'].lower()
                        if brand not in sheet_tags:
                            sheet_tags.add(brand)
                            sheet_brand_tags += 1
                    
                    if product.get('category'):
                        category = product['category'].lower()
                        if category not in sheet_tags:
                            sheet_tags.add(category)
                            sheet_category_tags += 1
                    
                    if product.get('subcategory'):
                        subcategory = product['subcategory'].lower()
                        if subcategory not in sheet_tags:
                            sheet_tags.add(subcategory)
                            sheet_category_tags += 1
                    
                    if product.get('name'):
                        words = product['name'].lower().split()
                        for word in words:
                            if len(word) > 3 and not word.isdigit() and word not in sheet_tags:
                                sheet_tags.add(word)
                                sheet_word_tags += 1

                logger.info(f"=== TAG GENERATION STATS (Sheet '{sheet_name}') ===")
                logger.info(f"Total unique tags: {len(sheet_tags)}")
                logger.info(f"  - SKU tags: {sheet_sku_tags}")
                logger.info(f"  - Brand tags: {sheet_brand_tags}")
                logger.info(f"  - Category/Subcategory tags: {sheet_category_tags}")
                logger.info(f"  - Word tags from names: {sheet_word_tags}")
                
                all_tags.update(sheet_tags)
                total_sku_tags += sheet_sku_tags
                total_brand_tags += sheet_brand_tags
                total_category_tags += sheet_category_tags
                total_word_tags += sheet_word_tags

                all_products.extend(products)

                sheets_info.append({
                    'name': sheet_name,
                    'rows': len(df),
                    'products': len(products),
                    'products_with_sku': products_with_sku,
                    'products_without_sku': products_without_sku,
                    'unique_tags': len(sheet_tags),
                    'status': 'processed',
                    'detected_columns': list(detected_columns.keys())
                })

                logger.info(f"Sheet '{sheet_name}': extracted {len(products)} products")

            if not all_products:
                return {
                    "success": False,
                    "error": "No products extracted from any sheet",
                    "sheets_info": sheets_info
                }

            unique_products = {}
            duplicate_sku_count = 0
            no_sku_count = 0
            
            for product in all_products:
                sku = product.get('sku', '')
                if sku and sku not in unique_products:
                    unique_products[sku] = product
                elif sku and sku in unique_products:
                    duplicate_sku_count += 1
                elif not sku:
                    unique_products[f"no_sku_{len(unique_products)}"] = product
                    no_sku_count += 1

            final_products = list(unique_products.values())

            logger.info(f"")
            logger.info(f"========================================")
            logger.info(f"=== FINAL STATISTICS ===")
            logger.info(f"========================================")
            logger.info(f"Total sheets processed: {len(sheets_info)}")
            logger.info(f"Total rows read: {total_rows}")
            logger.info(f"Total products extracted: {len(all_products)}")
            logger.info(f"Unique products (after deduplication): {len(final_products)}")
            logger.info(f"Duplicate SKUs removed: {duplicate_sku_count}")
            logger.info(f"Products without SKU: {no_sku_count}")
            logger.info(f"")
            logger.info(f"=== TAG STATISTICS ===")
            logger.info(f"Total UNIQUE tags: {len(all_tags)}")
            logger.info(f"  - SKU tags: {total_sku_tags}")
            logger.info(f"  - Brand tags: {total_brand_tags}")
            logger.info(f"  - Category/Subcategory tags: {total_category_tags}")
            logger.info(f"  - Word tags from names: {total_word_tags}")
            logger.info(f"")
            logger.info(f"Tag distribution:")
            if len(final_products) > 0:
                logger.info(f"  - Average tags per product: {len(all_tags) / len(final_products):.1f}")
            logger.info(f"  - SKU coverage: {(total_sku_tags / len(final_products) * 100):.1f}%")
            logger.info(f"========================================")

            return {
                "success": True,
                "total_rows": total_rows,
                "products_count": len(final_products),
                "products": final_products,
                "tags": sorted(list(all_tags)),
                "sheets_info": sheets_info,
                "statistics": {
                    "total_products": len(all_products),
                    "unique_products": len(final_products),
                    "duplicate_skus": duplicate_sku_count,
                    "products_without_sku": no_sku_count,
                    "total_tags": len(all_tags),
                    "sku_tags": total_sku_tags,
                    "brand_tags": total_brand_tags,
                    "category_tags": total_category_tags,
                    "word_tags": total_word_tags
                }
            }

        except Exception as e:
            logger.error(f"Error parsing file: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _parse_excel_all_sheets(self, file_path: str) -> Dict:
        """Парсит Excel файл - ВСЕ ЛИСТЫ."""
        dataframes = []
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            logger.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
            
            for sheet_name in sheet_names:
                try:
                    logger.info(f"Parsing sheet: '{sheet_name}'")
                    
                    df_sheet = pd.read_excel(
                        file_path, 
                        sheet_name=sheet_name, 
                        header=None, 
                        nrows=self.max_rows
                    )
                    
                    df_sheet = df_sheet.dropna(how='all')
                    if df_sheet.empty:
                        logger.info(f"Sheet '{sheet_name}' is empty, skipping")
                        continue
                    
                    df_sheet = df_sheet.dropna(axis=1, how='all')
                    if df_sheet.empty:
                        logger.info(f"Sheet '{sheet_name}' has no data columns, skipping")
                        continue
                    
                    header_row = self._find_header_row(df_sheet)
                    
                    new_columns = df_sheet.iloc[header_row].values
                    new_columns = self._make_unique_columns(new_columns)
                    df_sheet.columns = new_columns
                    df_sheet = df_sheet.iloc[header_row + 1:].reset_index(drop=True)
                    
                    df_sheet = df_sheet.dropna(how='all')
                    
                    if not df_sheet.empty:
                        logger.info(f"Sheet '{sheet_name}': {len(df_sheet)} rows, {len(df_sheet.columns)} columns")
                        dataframes.append({
                            'sheet': sheet_name,
                            'df': df_sheet
                        })
                    
                except Exception as e:
                    logger.warning(f"Error parsing sheet '{sheet_name}': {e}")
                    continue
            
            return {'dataframes': dataframes}
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return {'dataframes': []}

    def _make_unique_columns(self, columns) -> List[str]:
        """Делает названия колонок уникальными."""
        seen = {}
        result = []
        for col in columns:
            col_str = str(col) if not pd.isna(col) else 'unnamed'
            if col_str in seen:
                seen[col_str] += 1
                result.append(f"{col_str}_{seen[col_str]}")
            else:
                seen[col_str] = 0
                result.append(col_str)
        return result

    async def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """Парсит CSV файл."""
        try:
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
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            return pd.DataFrame()

    async def _parse_pdf(self, file_path: str) -> pd.DataFrame:
        """Парсит PDF файл с таблицами."""
        all_tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:50]:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if len(table) > 1:
                                df = pd.DataFrame(table[1:], columns=table[0])
                                all_tables.append(df)

            if all_tables:
                df = pd.concat(all_tables, ignore_index=True)
                return df
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
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
            try:
                df = pd.read_csv(
                    file_path,
                    delim_whitespace=True,
                    encoding=self.default_encoding,
                    nrows=self.max_rows,
                    on_bad_lines='skip'
                )
                return df.dropna(how='all')
            except Exception as e:
                logger.error(f"Error parsing TXT: {e}")
                return pd.DataFrame()

    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Умно находит строку с заголовками."""
        import re

        header_keywords = [
            'артикул', 'sku', 'код', 'article', 'арт', 'код товара', 'vendor', 'партномер',
            'код для заказа', 'каталожный номер', 'item', 'part number',
            'наименование', 'название', 'name', 'товар', 'продукт', 'описание',
            'номенклатура', 'материал', 'наименование товара',
            'цена', 'price', 'стоимость', 'прайс', 'ррц', 'розница', 'опт',
            'бренд', 'brand', 'производитель', 'марка', 'manufacturer', 'vendor', 'завод',
            'категория', 'category', 'группа', 'раздел', 'тип', 'вид', 'рубрика',
            'подгруппа', 'подкатегория', 'subcategory',
            'единица', 'unit', 'ед', 'ед.изм', 'единица измерения',
            'остаток', 'stock', 'наличие', 'количество', 'qty', 'available', 'склад',
            'url', 'ссылка', 'link', 'href'
        ]
        
        best_row = 0
        best_score = 0

        for i in range(min(50, len(df))):
            row = df.iloc[i]
            score = 0
            row_values = [str(v).lower().strip() for v in row if not pd.isna(v)]

            if len(row_values) == 0:
                continue

            fill_pct = len(row_values) / len(row)
            if fill_pct < 0.2:
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
            if 3 < avg_len < 40:
                score += 10
            elif avg_len > 60:
                score -= 20

            numeric_count = 0
            for val in row_values:
                try:
                    float(str(val).replace(',', '.').replace(' ', '').replace('\xa0', ''))
                    numeric_count += 1
                except:
                    pass

            if len(row_values) > 0 and numeric_count / len(row_values) < 0.4:
                score += 15
            else:
                score -= 10

            if score > best_score:
                best_score = score
                best_row = i

        logger.info(f"Header detection: found row {best_row} with score {best_score}")
        if best_row < len(df):
            logger.info(f"Header row values: {df.iloc[best_row].tolist()[:8]}")

        return best_row

    def _normalize_text(self, text: str) -> str:
        """Нормализует текст товара."""
        import re

        if not text or pd.isna(text):
            return ""

        text = str(text)
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _extract_url(self, row) -> Optional[str]:
        """Извлекает URL из строки (legacy метод)."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        
        if isinstance(row, pd.Series):
            row_values = row.values
        elif isinstance(row, dict):
            row_values = row.values()
        else:
            return None
        
        for val in row_values:
            if pd.isna(val):
                continue
            val_str = str(val)
            match = re.search(url_pattern, val_str)
            if match:
                return match.group(0)
        return None

    def _extract_url_from_dict(self, row_dict: Dict) -> Optional[str]:
        """Извлекает URL из словаря значений строки."""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        
        for val in row_dict.values():
            if val is None:
                continue
            val_str = str(val)
            match = re.search(url_pattern, val_str)
            if match:
                return match.group(0)
        return None

    def _extract_products(self, df: pd.DataFrame, detected_columns: Dict[str, str], sheet_name: str = '') -> List[Dict]:
        """Извлекает товары из DataFrame."""
        products = []
        
        has_sku = 'sku' in detected_columns
        has_name = 'name' in detected_columns
        
        logger.info(f"=== PRODUCT EXTRACTION START ===")
        logger.info(f"Has SKU column: {has_sku}")
        logger.info(f"Has NAME column: {has_name}")
        logger.info(f"Detected columns: {list(detected_columns.keys())}")

        for idx in df.index:
            try:
                product = {}
                product['source_sheet'] = sheet_name

                def safe_get_value(df, idx, col_name):
                    """Безопасно извлекает значение из DataFrame"""
                    if col_name not in df.columns:
                        return None
                    val = df.loc[idx, col_name]
                    if isinstance(val, pd.Series):
                        return val.iloc[0] if not val.empty else None
                    return val

                if has_sku:
                    sku = safe_get_value(df, idx, 'sku')
                    if pd.notna(sku):
                        sku_str = str(sku).strip()
                        if sku_str and sku_str.lower() != 'nan':
                            product['sku'] = sku_str

                if has_name:
                    name = safe_get_value(df, idx, 'name')
                    if pd.isna(name):
                        continue
                    name_str = str(name).strip()
                    if not name_str or name_str.lower() == 'nan':
                        continue
                    product['name'] = self._normalize_text(name_str)
                else:
                    continue

                if 'brand' in detected_columns:
                    brand = safe_get_value(df, idx, 'brand')
                    if pd.notna(brand):
                        brand_str = str(brand).strip()
                        if brand_str and brand_str.lower() != 'nan':
                            product['brand'] = brand_str

                if 'category' in detected_columns:
                    category = safe_get_value(df, idx, 'category')
                    if pd.notna(category):
                        cat_str = str(category).strip()
                        if cat_str and cat_str.lower() != 'nan':
                            product['category'] = cat_str

                if 'subcategory' in detected_columns:
                    subcategory = safe_get_value(df, idx, 'subcategory')
                    if pd.notna(subcategory):
                        subcat_str = str(subcategory).strip()
                        if subcat_str and subcat_str.lower() != 'nan':
                            product['subcategory'] = subcat_str

                if 'unit' in detected_columns:
                    unit = safe_get_value(df, idx, 'unit')
                    if pd.notna(unit):
                        unit_str = str(unit).strip()
                        if unit_str:
                            product['unit'] = unit_str

                if 'stock' in detected_columns:
                    stock = safe_get_value(df, idx, 'stock')
                    if pd.notna(stock):
                        try:
                            stock_str = str(stock).replace('>', '').replace('<', '').replace(' ', '').replace('\xa0', '')
                            product['stock'] = int(float(stock_str))
                        except:
                            pass

                if 'price' in detected_columns:
                    price = safe_get_value(df, idx, 'price')
                    if pd.notna(price):
                        try:
                            price_str = str(price).replace(' ', '').replace('\xa0', '').replace(',', '.').replace('₽', '').replace('р', '').replace('руб', '')
                            product['price'] = float(price_str)
                        except:
                            pass

                try:
                    row_dict = {}
                    for col in df.columns:
                        val = safe_get_value(df, idx, col)
                        if pd.notna(val):
                            row_dict[col] = val
                    url = self._extract_url_from_dict(row_dict)
                    if url:
                        product['url'] = url
                except Exception as e:
                    logger.debug(f"Could not extract URL from row {idx}: {e}")

                raw_parts = []
                for col in df.columns:
                    val = safe_get_value(df, idx, col)
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if val_str and val_str.lower() != 'nan':
                            raw_parts.append(val_str)
                product['raw_text'] = ' '.join(raw_parts)

                tags = set()
                if product.get('sku'):
                    tags.add(product['sku'])
                if product.get('brand'):
                    tags.add(product['brand'].lower())
                if product.get('category'):
                    tags.add(product['category'].lower())
                if product.get('subcategory'):
                    tags.add(product['subcategory'].lower())
                if product.get('name'):
                    for word in product['name'].lower().split():
                        if len(word) > 3 and not word.isdigit():
                            tags.add(word)
                product['tags'] = list(tags)

                product['row_number'] = int(idx) + 1
                products.append(product)

            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue

        logger.info(f"Extracted {len(products)} products from sheet '{sheet_name}'")
        return products

price_list_parser = PriceListParser()
