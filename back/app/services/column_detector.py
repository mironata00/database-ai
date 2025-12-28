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
        self.synonyms_map = settings.COLUMN_SYNONYMS_MAP
        self.fuzzy_matching = settings.PARSING_COLUMN_FUZZY_MATCHING
        self.min_confidence = settings.PARSING_COLUMN_MIN_CONFIDENCE
        self.use_position_hints = settings.PARSING_COLUMN_USE_POSITION_HINTS
    
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Определяет колонки в DataFrame.
        
        Args:
            df: pandas DataFrame с данными
            
        Returns:
            Dict[column_type, column_name] - маппинг типов на названия колонок
        """
        columns = df.columns.tolist()
        detected = {}
        
        logger.info(f"Detecting columns from: {columns}")
        
        # Проходим по каждому типу колонки
        for column_type, synonyms in self.synonyms_map.items():
            best_match = self._find_best_match(columns, synonyms, column_type)
            
            if best_match:
                detected[column_type] = best_match
                logger.info(f"Detected '{column_type}' as column '{best_match}'")
        
        # Проверяем обязательные колонки
        required_columns = settings.PARSING_REQUIRED_COLUMNS_LIST
        missing_columns = [col for col in required_columns if col not in detected]
        
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            # Попытка определить по содержимому
            detected.update(self._detect_by_content(df, missing_columns))
        
        return detected
    
    def _find_best_match(
        self, 
        columns: List[str], 
        synonyms: List[str],
        column_type: str
    ) -> Optional[str]:
        """
        Находит наилучшее совпадение колонки с синонимами.
        
        Args:
            columns: Список названий колонок
            synonyms: Список синонимов для искомой колонки
            column_type: Тип колонки (для position hints)
            
        Returns:
            Название колонки или None
        """
        best_column = None
        best_score = 0.0
        
        for col in columns:
            col_normalized = self._normalize_column_name(col)
            
            # Точное совпадение
            if col_normalized in synonyms:
                return col
            
            # Частичное совпадение (содержит синоним)
            for synonym in synonyms:
                if synonym in col_normalized or col_normalized in synonym:
                    score = 0.9
                    if score > best_score:
                        best_score = score
                        best_column = col
            
            # Нечеткое совпадение (если включено)
            if self.fuzzy_matching:
                for synonym in synonyms:
                    similarity = SequenceMatcher(None, col_normalized, synonym).ratio()
                    
                    # Бонус за позицию колонки (если включено)
                    if self.use_position_hints:
                        position_bonus = self._get_position_bonus(
                            columns.index(col), 
                            len(columns),
                            column_type
                        )
                        similarity += position_bonus
                    
                    if similarity > best_score and similarity >= self.min_confidence:
                        best_score = similarity
                        best_column = col
        
        return best_column if best_score >= self.min_confidence else None
    
    def _normalize_column_name(self, name: str) -> str:
        """
        Нормализует название колонки.
        
        Args:
            name: Исходное название
            
        Returns:
            Нормализованное название (lowercase, без лишних символов)
        """
        # Приводим к нижнему регистру
        name = str(name).lower()
        
        # Убираем лишние пробелы
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Убираем спецсимволы (кроме букв, цифр, пробелов)
        name = re.sub(r'[^\w\s]', '', name, flags=re.UNICODE)
        
        return name
    
    def _get_position_bonus(
        self, 
        position: int, 
        total_columns: int,
        column_type: str
    ) -> float:
        """
        Возвращает бонус к score в зависимости от позиции колонки.
        
        Эвристика:
        - SKU обычно в первых колонках
        - Name обычно после SKU
        - Price обычно в конце или в середине
        
        Args:
            position: Индекс колонки
            total_columns: Общее количество колонок
            column_type: Тип колонки
            
        Returns:
            Бонус от 0.0 до 0.1
        """
        position_ratio = position / total_columns if total_columns > 0 else 0
        
        position_hints = {
            "sku": (0.0, 0.2),      # В первых 20%
            "name": (0.1, 0.4),     # В первых 10-40%
            "price": (0.3, 0.8),    # В диапазоне 30-80%
            "brand": (0.0, 0.5),    # В первой половине
            "category": (0.0, 0.5), # В первой половине
            "unit": (0.4, 0.9),     # Ближе к концу
            "stock": (0.6, 1.0),    # В конце
        }
        
        if column_type in position_hints:
            min_pos, max_pos = position_hints[column_type]
            if min_pos <= position_ratio <= max_pos:
                return 0.1
        
        return 0.0
    
    def _detect_by_content(
        self, 
        df: pd.DataFrame, 
        missing_columns: List[str]
    ) -> Dict[str, str]:
        """
        Определяет колонки по содержимому (fallback метод).
        
        Args:
            df: DataFrame
            missing_columns: Список недостающих типов колонок
            
        Returns:
            Dict[column_type, column_name]
        """
        detected = {}
        
        # Берем первые 100 строк для анализа
        sample = df.head(100)
        
        for column_type in missing_columns:
            for col in df.columns:
                if col in detected.values():
                    continue
                
                if self._check_content_match(sample[col], column_type):
                    detected[column_type] = col
                    logger.info(
                        f"Detected '{column_type}' as '{col}' by content analysis"
                    )
                    break
        
        return detected
    
    def _check_content_match(self, series: pd.Series, column_type: str) -> bool:
        """
        Проверяет соответствие содержимого колонки типу.
        
        Args:
            series: pandas Series
            column_type: Тип колонки
            
        Returns:
            True если содержимое соответствует типу
        """
        # Убираем NaN значения
        series = series.dropna()
        if len(series) == 0:
            return False
        
        if column_type == "sku":
            # Артикулы обычно содержат буквы и цифры, часто дефисы
            pattern = r'^[A-Za-z0-9\-_]+$'
            matches = series.astype(str).str.match(pattern).sum()
            return matches / len(series) > 0.7
        
        elif column_type == "name":
            # Наименования - длинный текст (>10 символов в среднем)
            avg_length = series.astype(str).str.len().mean()
            return avg_length > 10
        
        elif column_type == "price":
            # Цены - числа (возможно с валютой)
            try:
                # Попытка преобразовать в float
                numeric = pd.to_numeric(series, errors='coerce')
                valid_nums = numeric.notna().sum()
                return valid_nums / len(series) > 0.7
            except:
                return False
        
        elif column_type == "stock":
            # Остатки - целые числа
            try:
                numeric = pd.to_numeric(series, errors='coerce')
                valid_nums = numeric.notna().sum()
                if valid_nums / len(series) > 0.7:
                    # Проверяем что в основном целые числа
                    integers = (numeric == numeric.astype(int)).sum()
                    return integers / valid_nums > 0.9
            except:
                return False
        
        return False
    
    def get_mapping_report(self, detected: Dict[str, str]) -> str:
        """
        Возвращает отчет о найденных колонках.
        
        Args:
            detected: Словарь с найденными колонками
            
        Returns:
            Текстовый отчет
        """
        report = ["Column Detection Report:", "=" * 50]
        
        for column_type in ["sku", "name", "price", "brand", "category", "unit", "stock"]:
            if column_type in detected:
                report.append(f"✓ {column_type:12} -> '{detected[column_type]}'")
            else:
                report.append(f"✗ {column_type:12} -> NOT FOUND")
        
        # Проверка обязательных колонок
        required = settings.PARSING_REQUIRED_COLUMNS_LIST
        missing_required = [col for col in required if col not in detected]
        
        if missing_required:
            report.append("")
            report.append(f"⚠ WARNING: Missing required columns: {', '.join(missing_required)}")
        
        return "\n".join(report)


# Singleton instance
column_detector = ColumnDetector()
