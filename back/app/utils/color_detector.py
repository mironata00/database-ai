"""
Автоматическое определение цвета поставщика по тегам
"""
from typing import List

# Категории и их ключевые слова
CATEGORY_KEYWORDS = {
    'water': {
        'color': '#3B82F6',  # Синий/Голубой
        'keywords': [
            'вод', 'душ', 'смеситель', 'кран', 'сантехник', 'канализ', 
            'водопровод', 'труб', 'фитинг', 'насос', 'бойлер', 'водонагрев',
            'унитаз', 'раковин', 'ванн', 'слив', 'фильтр', 'счетчик воды'
        ]
    },
    'electric': {
        'color': '#EAB308',  # Желтый
        'keywords': [
            'электр', 'свет', 'лампа', 'провод', 'кабель', 'розетк', 
            'выключател', 'автомат', 'щит', 'освещени', 'led', 'светодиод',
            'трансформатор', 'генератор', 'ток', 'напряжени', 'энерг'
        ]
    },
    'wood': {
        'color': '#92400E',  # Коричневый
        'keywords': [
            'дерев', 'пиломатериал', 'доск', 'брус', 'фанер', 'дсп', 'мдф',
            'паркет', 'ламинат', 'вагонк', 'осб', 'двп', 'столярн', 'мебель'
        ]
    },
    'chemical': {
        'color': '#9333EA',  # Фиолетовый
        'keywords': [
            'химич', 'краск', 'лак', 'растворител', 'клей', 'герметик',
            'мастик', 'грунт', 'эмаль', 'пропитк', 'антисептик', 'реагент'
        ]
    }
}

DEFAULT_COLOR = '#6B7280'  # Серый по умолчанию


def detect_color_from_tags(tags: List[str]) -> str:
    """
    Определяет цвет поставщика на основе тегов
    
    Args:
        tags: Список тегов поставщика
        
    Returns:
        Hex-код цвета
    """
    if not tags:
        return DEFAULT_COLOR
    
    # Подсчитываем совпадения для каждой категории
    category_scores = {category: 0 for category in CATEGORY_KEYWORDS.keys()}
    
    tags_lower = [tag.lower() for tag in tags]
    
    for category, data in CATEGORY_KEYWORDS.items():
        for keyword in data['keywords']:
            for tag in tags_lower:
                if keyword in tag:
                    category_scores[category] += 1
    
    # Находим категорию с максимальным количеством совпадений
    max_category = max(category_scores.items(), key=lambda x: x[1])
    
    if max_category[1] > 0:
        return CATEGORY_KEYWORDS[max_category[0]]['color']
    
    return DEFAULT_COLOR


def get_color_name(hex_color: str) -> str:
    """Возвращает название цвета по hex-коду"""
    color_names = {
        '#3B82F6': 'Синий (Вода)',
        '#EAB308': 'Желтый (Электрика)',
        '#92400E': 'Коричневый (Дерево)',
        '#9333EA': 'Фиолетовый (Химия)',
        '#6B7280': 'Серый (Разное)'
    }
    return color_names.get(hex_color, 'Неизвестный')


def get_available_colors() -> List[dict]:
    """Возвращает список доступных цветов для выбора"""
    return [
        {'hex': '#3B82F6', 'name': 'Синий (Вода)', 'category': 'water'},
        {'hex': '#EAB308', 'name': 'Желтый (Электрика)', 'category': 'electric'},
        {'hex': '#92400E', 'name': 'Коричневый (Дерево)', 'category': 'wood'},
        {'hex': '#9333EA', 'name': 'Фиолетовый (Химия)', 'category': 'chemical'},
        {'hex': '#6B7280', 'name': 'Серый (Разное)', 'category': 'other'},
        {'hex': '#EF4444', 'name': 'Красный', 'category': 'custom'},
        {'hex': '#10B981', 'name': 'Зеленый', 'category': 'custom'},
        {'hex': '#F59E0B', 'name': 'Оранжевый', 'category': 'custom'},
    ]
