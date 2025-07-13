# src/ocr.py - Исправленный OCR с совместимыми языковыми группами
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import easyocr
import pytesseract
from typing import Optional, List, Tuple, Dict
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    print("PaddleOCR не установлен")

class TextExtractor:
    def __init__(self):
        """Инициализация OCR моделей с совместимыми языковыми группами"""
        # Словари для разных групп совместимых языков в EasyOCR
        self.easy_ocr_readers = {}
        self._init_models()
    
    def _init_models(self):
        """Инициализация OCR моделей с учетом совместимости языков"""
        
        # Инициализируем EasyOCR для разных групп совместимых языков
        try:
            # Группа 1: Азиатские языки (японский, корейский) + английский
            self.easy_ocr_readers['asian'] = easyocr.Reader(['ja', 'ko', 'en'], gpu=False)
            print("✅ EasyOCR азиатские языки загружены: японский, корейский, английский")
        except Exception as e:
            print(f"❌ Ошибка загрузки азиатских языков EasyOCR: {e}")
            self.easy_ocr_readers['asian'] = None

        try:
            # Группа 2: Китайский + английский (китайский совместим только с английским)
            self.easy_ocr_readers['chinese'] = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            print("✅ EasyOCR китайский загружен: китайский упрощенный, английский")
        except Exception as e:
            print(f"❌ Ошибка загрузки китайского EasyOCR: {e}")
            self.easy_ocr_readers['chinese'] = None

        try:
            # Группа 3: Европейские языки (русский, английский)
            self.easy_ocr_readers['european'] = easyocr.Reader(['ru', 'en'], gpu=False)
            print("✅ EasyOCR европейские языки загружены: русский, английский")
        except Exception as e:
            print(f"❌ Ошибка загрузки европейских языков EasyOCR: {e}")
            self.easy_ocr_readers['european'] = None

        # Fallback: только английский, если ничего не загрузилось
        if not any(self.easy_ocr_readers.values()):
            try:
                self.easy_ocr_readers['fallback'] = easyocr.Reader(['en'], gpu=False)
                print("⚠️ EasyOCR fallback: только английский")
            except Exception as e:
                print(f"❌ Критическая ошибка EasyOCR: {e}")
                self.easy_ocr_readers['fallback'] = None

        # Проверяем Tesseract
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract доступен")
        except Exception as e:
            print(f"❌ Tesseract недоступен: {e}")
    
    def _get_easyocr_reader(self, language: str):
        """Получает подходящий EasyOCR reader для языка"""
        if language in ['ja', 'ko']:
            return self.easy_ocr_readers.get('asian')
        elif language == 'zh':
            return self.easy_ocr_readers.get('chinese') 
        elif language in ['ru', 'en']:
            return self.easy_ocr_readers.get('european')
        else:
            # Fallback на любой доступный reader
            for reader in self.easy_ocr_readers.values():
                if reader is not None:
                    return reader
            return None
    
    def extract_text_simple(self, image_path: str, bbox: List[int], language: str) -> str:
        """
        Простое извлечение текста БЕЗ автоопределения языка
        
        Args:
            image_path: путь к изображению
            bbox: координаты области [x1, y1, x2, y2]
            language: ВЫБРАННЫЙ ПОЛЬЗОВАТЕЛЕМ язык ('ja', 'ko', 'zh', 'en', 'ru')
            
        Returns:
            Распознанный текст
        """
        logger.info(f"Извлечение текста на языке {language} из области {bbox}")
        
        try:
            # Загружаем и обрезаем изображение
            image = Image.open(image_path)
            x1, y1, x2, y2 = bbox
            
            if x2 - x1 < 5 or y2 - y1 < 5:
                return ""
            
            cropped = image.crop((x1, y1, x2, y2))
            
            # Простая предобработка
            if cropped.mode != 'RGB':
                cropped = cropped.convert('RGB')
            
            # Увеличиваем если маленькое
            width, height = cropped.size
            if width < 50 or height < 25:
                cropped = cropped.resize((width * 3, height * 3), Image.LANCZOS)
            
            # Увеличиваем контраст
            enhancer = ImageEnhance.Contrast(cropped)
            processed = enhancer.enhance(1.5)
            
            # Сначала пробуем Tesseract для выбранного языка (обычно лучше работает)
            tesseract_result = self._extract_with_tesseract(processed, language)
            if tesseract_result:
                return tesseract_result
            
            # Если Tesseract не сработал, пробуем EasyOCR
            easyocr_result = self._extract_with_easyocr(processed, language)
            if easyocr_result:
                return easyocr_result
            
            logger.warning(f"Текст не распознан на языке {language}")
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return ""
    
    def _extract_with_tesseract(self, image: Image.Image, language: str) -> str:
        """Извлечение с Tesseract для конкретного языка"""
        try:
            # Маппинг языков для Tesseract
            tesseract_langs = {
                'ja': 'jpn',
                'ko': 'kor', 
                'zh': 'chi_sim',
                'en': 'eng',
                'ru': 'rus'
            }
            
            tesseract_lang = tesseract_langs.get(language, 'eng')
            
            # Разные конфигурации для разных типов текста
            configs = [
                r'--oem 3 --psm 6',  # Блок текста
                r'--oem 3 --psm 8',  # Одно слово
                r'--oem 3 --psm 7',  # Одна строка
            ]
            
            best_result = ""
            best_length = 0
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(
                        image, lang=tesseract_lang, config=config
                    ).strip()
                    
                    if len(text) > best_length and len(text) > 1:
                        # Простая очистка
                        cleaned = re.sub(r'\s+', ' ', text.strip())
                        if cleaned and len(cleaned) > 1:
                            best_result = cleaned
                            best_length = len(cleaned)
                
                except Exception as e:
                    continue
            
            if best_result:
                logger.info(f"✅ Tesseract ({tesseract_lang}): '{best_result}'")
                return best_result
            
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка Tesseract для {language}: {e}")
            return ""
    
    def _extract_with_easyocr(self, image: Image.Image, language: str) -> str:
        """Извлечение с EasyOCR для конкретного языка"""
        # Получаем подходящий reader для языка
        reader = self._get_easyocr_reader(language)
        
        if not reader:
            logger.warning(f"EasyOCR reader не доступен для языка {language}")
            return ""
        
        try:
            img_array = np.array(image)
            results = reader.readtext(img_array, detail=1)
            
            if results:
                # Берем результат с наибольшей уверенностью
                best_result = max(results, key=lambda x: x[2])
                text = best_result[1].strip()
                confidence = best_result[2]
                
                if text and len(text) > 1 and confidence > 0.3:
                    # Простая очистка
                    cleaned = re.sub(r'\s+', ' ', text.strip())
                    logger.info(f"✅ EasyOCR ({language}): '{cleaned}' (conf: {confidence:.2f})")
                    return cleaned
            
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка EasyOCR для {language}: {e}")
            return ""
    
    # Обратная совместимость
    def extract_text(self, image_path: str, bbox: List[int], language: str = 'en') -> str:
        """Обратная совместимость"""
        return self.extract_text_simple(image_path, bbox, language)