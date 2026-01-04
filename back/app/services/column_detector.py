"""
Column Detection Service
Автоматическое определение колонок в прайс-листах с поддержкой синонимов
"""
from typing import Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher
import pandas as pd
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ColumnDetector:
    """Детектор колонок с поддержкой синонимов и нечеткого поиска."""

    def __init__(self):
        self.extended_synonyms = {
            'sku': [
                'sku', 'артикул', 'код', 'article', 'арт', 'код товара',
                'артикул товара', 'vendor code', 'item code', 'part number',
                'партномер', 'каталожный номер', 'код для заказа', 'item',
                'vendor', 'артикул производителя', 'код производителя',
                'внутренний код', 'ref', 'reference', 'product code'
            ],
            'name': [
                'name', 'наименование', 'название', 'товар', 'продукт',
                'описание', 'product', 'item', 'description', 'номенклатура',
                'материал', 'наименование товара', 'товар/услуга', 'позиция',
                'product name', 'item name', 'title', 'заголовок'
            ],
            'price': [
                'price', 'цена', 'стоимость', 'прайс', 'cost', 'розница',
                'опт', 'розничная цена', 'оптовая цена', 'price rub',
                'цена руб', 'ррц', 'рекомендуемая цена', 'базовая цена',
                'цена с ндс', 'цена без ндс', 'unit price', 'сумма'
            ],
            'brand': [
                'brand', 'бренд', 'производитель', 'марка', 'manufacturer',
                'vendor', 'поставщик', 'завод', 'торговая марка', 'tm',
                'изготовитель', 'фирма', 'компания производитель'
            ],
            'category': [
                'category', 'категория', 'группа', 'раздел', 'тип', 'вид',
                'class', 'group', 'рубрика', 'рубрика в каталоге',
                'товарная группа', 'группа товаров', 'классификация'
            ],
            'subcategory': [
                'subcategory', 'подкатегория', 'подгруппа', 'подраздел',
                'subgroup', 'sub category', 'рубрика в каталоге_1',
                'детальная категория', 'подвид'
            ],
            'unit': [
                'unit', 'ед', 'единица', 'единица измерения', 'ед.изм',
                'measure', 'uom', 'ед. изм.', 'единицы', 'шт', 'штук'
            ],
            'stock': [
                'stock', 'остаток', 'наличие', 'количество', 'qty',
                'available', 'в наличии', 'склад', 'остатки', 'кол-во',
                'quantity', 'доступно', 'свободно', 'резерв'
            ],
            'url': [
                'url', 'ссылка', 'link', 'href', 'адрес', 'web',
                'website', 'страница', 'page', 'uri'
            ]
        }

        self.fuzzy_matching = settings.PARSING_COLUMN_FUZZY_MATCHING
        self.min_confidence = settings.PARSING_COLUMN_MIN_CONFIDENCE
        self.use_position_hints = settings.PARSING_COLUMN_USE_POSITION_HINTS

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Определяет колонки в DataFrame."""
        columns = df.columns.tolist()
        detected = {}
        used_columns = set()

        logger.info(f"=== COLUMN DETECTION START ===")
        logger.info(f"Total columns: {len(columns)}")
        logger.info(f"Column names: {columns[:15]}...")

        priority_order = ['sku', 'name', 'brand', 'category', 'subcategory', 'price', 'unit', 'stock', 'url']

        for column_type in priority_order:
            synonyms = self.extended_synonyms.get(column_type, [])
            best_match = self._find_best_match(columns, synonyms, column_type, used_columns)

            if best_match:
                detected[column_type] = best_match
                used_columns.add(best_match)
                logger.info(f"Detected '{column_type}' -> '{best_match}'")

        required_columns = ['name']
        missing_columns = [col for col in required_columns if col not in detected]

        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            detected.update(self._detect_by_content(df, missing_columns, used_columns))

        logger.info(f"=== COLUMN DETECTION COMPLETE ===")
        logger.info(f"Detected: {detected}")
        return detected

    def _find_best_match(
        self,
        columns: List[str],
        synonyms: List[str],
        column_type: str,
        used_columns: set
    ) -> Optional[str]:
        """Находит наилучшее совпадение колонки с синонимами."""
        best_column = None
        best_score = 0.0

        for col in columns:
            if col in used_columns:
                continue

            col_normalized = self._normalize_column_name(col)

            if not col_normalized:
                continue

            if col_normalized in synonyms:
                return col

            for synonym in synonyms:
                if synonym in col_normalized or col_normalized in synonym:
                    score = 0.9
                    if score > best_score:
                        best_score = score
                        best_column = col

            if self.fuzzy_matching:
                for synonym in synonyms:
                    similarity = SequenceMatcher(None, col_normalized, synonym).ratio()

                    if self.use_position_hints:
                        try:
                            position_bonus = self._get_position_bonus(
                                columns.index(col),
                                len(columns),
                                column_type
                            )
                            similarity += position_bonus
                        except:
                            pass

                    if similarity > best_score and similarity >= self.min_confidence:
                        best_score = similarity
                        best_column = col

        return best_column if best_score >= self.min_confidence else None

    def _normalize_column_name(self, name: str) -> str:
        """Нормализует название колонки."""
        if pd.isna(name):
            return ""

        name = str(name).lower()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s]', '', name, flags=re.UNICODE)

        return name

    def _get_position_bonus(
        self,
        position: int,
        total_columns: int,
        column_type: str
    ) -> float:
        """Возвращает бонус к score в зависимости от позиции колонки."""
        position_ratio = position / total_columns if total_columns > 0 else 0

        position_hints = {
            "sku": (0.0, 0.3),
            "name": (0.1, 0.5),
            "price": (0.3, 0.9),
            "brand": (0.0, 0.6),
            "category": (0.0, 0.4),
            "subcategory": (0.0, 0.5),
            "unit": (0.4, 0.9),
            "stock": (0.5, 1.0),
            "url": (0.7, 1.0),
        }

        if column_type in position_hints:
            min_pos, max_pos = position_hints[column_type]
            if min_pos <= position_ratio <= max_pos:
                return 0.1

        return 0.0

    def _detect_by_content(
        self,
        df: pd.DataFrame,
        missing_columns: List[str],
        used_columns: set
    ) -> Dict[str, str]:
        """Определяет колонки по содержимому (fallback метод)."""
        detected = {}
        sample = df.head(100)

        for column_type in missing_columns:
            for col in df.columns:
                if col in used_columns or col in detected.values():
                    continue

                try:
                    if self._check_content_match(sample[col], column_type):
                        detected[column_type] = col
                        used_columns.add(col)
                        logger.info(f"Detected '{column_type}' as '{col}' by content analysis")
                        break
                except:
                    continue

        return detected

    def _check_content_match(self, series: pd.Series, column_type: str) -> bool:
        """Проверяет соответствие содержимого колонки типу."""
        series = series.dropna()
        if len(series) == 0:
            return False

        if column_type == "sku":
            pattern = r'^[A-Za-zА-Яа-я0-9\-_\.]+$'
            matches = series.astype(str).str.match(pattern).sum()
            return matches / len(series) > 0.6

        elif column_type == "name":
            avg_length = series.astype(str).str.len().mean()
            return avg_length > 15

        elif column_type == "url":
            url_pattern = r'https?://'
            matches = series.astype(str).str.contains(url_pattern, regex=True).sum()
            return matches / len(series) > 0.5

        elif column_type == "stock":
            try:
                numeric = pd.to_numeric(series.astype(str).str.replace(r'[<>]', '', regex=True), errors='coerce')
                valid_nums = numeric.notna().sum()
                return valid_nums / len(series) > 0.5
            except:
                return False

        return False

    def get_mapping_report(self, detected: Dict[str, str]) -> str:
        """Возвращает отчет о найденных колонках."""
        report = ["Column Detection Report:", "=" * 50]

        column_types = ["sku", "name", "brand", "category", "subcategory", "price", "unit", "stock", "url"]

        for column_type in column_types:
            if column_type in detected:
                report.append(f"✓ {column_type:12} -> '{detected[column_type]}'")
            else:
                report.append(f"✗ {column_type:12} -> NOT FOUND")

        return "\n".join(report)


column_detector = ColumnDetector()
