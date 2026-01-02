import io
import logging
from typing import Optional
import pdfplumber
import pandas as pd
from PIL import Image
import pytesseract
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

class TextExtractor:
    """Извлечение текста из различных форматов файлов"""
    
    def extract_from_pdf(self, file_bytes: bytes) -> str:
        """Извлечение текста из PDF (только первая страница)"""
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                # Берем только первую страницу для реквизитов
                if pdf.pages:
                    page_text = pdf.pages[0].extract_text()
                    if page_text:
                        text = page_text
            
            logger.info(f"Extracted {len(text)} chars from PDF (first page)")
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""
    
    def extract_from_excel(self, file_bytes: bytes, filename: str) -> str:
        """Извлечение текста из Excel (только первые 20 строк + изображения)"""
        try:
            text_parts = []
            
            # Извлекаем текст из первых 20 строк
            if filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', nrows=20)
            elif filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd', nrows=20)
            else:
                df = pd.read_excel(io.BytesIO(file_bytes), nrows=20)
            
            # Добавляем текст из таблицы
            table_text = df.to_string(index=False)
            text_parts.append(table_text)
            
            # Извлекаем изображения из xlsx (только из первых строк)
            if filename.endswith('.xlsx'):
                try:
                    wb = load_workbook(io.BytesIO(file_bytes))
                    sheet = wb.active
                    
                    # Проходим по изображениям в первых 20 строках
                    for image in sheet._images:
                        # Проверяем что изображение в первых 20 строках
                        if hasattr(image, 'anchor') and hasattr(image.anchor, '_from'):
                            row = image.anchor._from.row
                            if row < 20:  # Только первые 20 строк
                                # Извлекаем изображение
                                img_data = image._data()
                                img = Image.open(io.BytesIO(img_data))
                                
                                # OCR распознавание
                                ocr_text = pytesseract.image_to_string(img, lang='rus+eng')
                                if ocr_text.strip():
                                    text_parts.append(f"\n[Текст из изображения]:\n{ocr_text}")
                                    logger.info(f"Extracted {len(ocr_text)} chars from image in Excel")
                    
                    wb.close()
                except Exception as e:
                    logger.warning(f"Could not extract images from Excel: {e}")
            
            result = "\n".join(text_parts)
            logger.info(f"Extracted {len(result)} chars from Excel (first 20 rows + images)")
            return result
            
        except Exception as e:
            logger.error(f"Excel extraction error: {e}")
            return ""
    
    def extract_from_image(self, file_bytes: bytes) -> str:
        """Извлечение текста из изображения через OCR"""
        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image, lang='rus+eng')
            logger.info(f"Extracted {len(text)} chars from image via OCR")
            return text
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return ""
    
    def extract_from_csv(self, file_bytes: bytes) -> str:
        """Извлечение текста из CSV (первые 20 строк)"""
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), nrows=20)
            text = df.to_string(index=False)
            logger.info(f"Extracted {len(text)} chars from CSV (first 20 rows)")
            return text
        except Exception as e:
            logger.error(f"CSV extraction error: {e}")
            return ""
    
    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Универсальный метод извлечения текста (только реквизиты, не весь прайс)"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return self.extract_from_pdf(file_bytes)
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return self.extract_from_excel(file_bytes, filename)
        elif filename_lower.endswith('.csv'):
            return self.extract_from_csv(file_bytes)
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            return self.extract_from_image(file_bytes)
        else:
            logger.warning(f"Unsupported file format: {filename}")
            return ""

text_extractor = TextExtractor()
