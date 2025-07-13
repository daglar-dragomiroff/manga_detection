# src/inpainting.py - Модуль для заливки и вставки текста на изображения
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional
import logging
import os

logger = logging.getLogger(__name__)

class TextInpainter:
    """Класс для заливки текста на изображениях манги"""
    
    def __init__(self):
        """Инициализация инпейнтера"""
        self.default_font_size = 16
        self.default_font_color = (0, 0, 0)  # Черный
        self.default_bg_color = (255, 255, 255)  # Белый фон
        self.fonts_cache = {}
        
    def inpaint_and_replace_text(self, 
                               image_path: str, 
                               results: List[Dict[str, Any]], 
                               text_settings: Dict[str, Any] = None) -> np.ndarray:
        """
        Главная функция: закрашивает оригинальный текст и вставляет перевод
        
        Args:
            image_path: путь к исходному изображению
            results: результаты OCR и перевода
            text_settings: настройки форматирования текста
            
        Returns:
            Обработанное изображение как numpy array
        """
        if not results:
            # Если нет результатов, возвращаем оригинал
            return np.array(Image.open(image_path))
        
        # Загружаем изображение
        image = Image.open(image_path).convert('RGB')
        
        # Применяем настройки по умолчанию
        settings = self._get_default_settings()
        if text_settings:
            settings.update(text_settings)
        
        logger.info(f"🎨 Начинаем заливку {len(results)} областей текста")
        
        # Обрабатываем каждую область текста
        for i, result in enumerate(results):
            if result.get('translated_text', '').strip():
                logger.info(f"🖌️ Заливка области #{i+1}: '{result['translated_text']}'")
                image = self._process_text_region(image, result, settings)
        
        return np.array(image)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Настройки текста по умолчанию"""
        return {
            'font_family': 'arial',
            'font_size': 16,
            'font_color': (0, 0, 0),      # Черный текст
            'bg_color': (255, 255, 255),  # Белый фон
            'stroke_width': 0,            # Толщина обводки
            'stroke_color': (0, 0, 0),    # Цвет обводки
            'padding': 5,                 # Отступы
            'alignment': 'center',        # Выравнивание
            'transparency': 1.0,          # Прозрачность фона (1.0 = непрозрачный)
            'auto_font_size': True,       # Автоматический размер шрифта
        }
    
    def _process_text_region(self, 
                           image: Image.Image, 
                           result: Dict[str, Any], 
                           settings: Dict[str, Any]) -> Image.Image:
        """Обработка одной текстовой области"""
        
        bbox = result['bbox']
        text = result['translated_text']
        
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        # Минимальная проверка размера
        if width < 10 or height < 10:
            logger.warning(f"⚠️ Слишком маленькая область: {width}x{height}")
            return image
        
        # 1. Закрашиваем исходную область
        image = self._inpaint_region(image, bbox, settings)
        
        # 2. Вставляем новый текст
        image = self._insert_text(image, bbox, text, settings)
        
        return image
    
    def _inpaint_region(self, 
                       image: Image.Image, 
                       bbox: List[int], 
                       settings: Dict[str, Any]) -> Image.Image:
        """Закрашивание области исходного текста"""
        
        x1, y1, x2, y2 = bbox
        bg_color = settings['bg_color']
        transparency = settings['transparency']
        
        # Создаем маску для закрашивания
        if transparency < 1.0:
            # Если есть прозрачность, используем более сложный метод
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Закрашиваем с прозрачностью
            alpha = int(255 * transparency)
            fill_color = (*bg_color, alpha)
            draw.rectangle([x1, y1, x2, y2], fill=fill_color)
            
            # Накладываем на оригинал
            image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        else:
            # Простое закрашивание
            draw = ImageDraw.Draw(image)
            draw.rectangle([x1, y1, x2, y2], fill=bg_color)
        
        return image
    
    def _insert_text(self, 
                    image: Image.Image, 
                    bbox: List[int], 
                    text: str, 
                    settings: Dict[str, Any]) -> Image.Image:
        """Вставка нового текста в область"""
        
        if not text.strip():
            return image
        
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        # Получаем шрифт
        font_size = settings['font_size']
        if settings['auto_font_size']:
            font_size = self._calculate_optimal_font_size(text, width, height, settings)
        
        font = self._get_font(settings['font_family'], font_size)
        
        # Подготавливаем текст (перенос строк для длинного текста)
        wrapped_text = self._wrap_text(text, font, width - settings['padding'] * 2)
        
        # Рассчитываем позицию
        text_x, text_y = self._calculate_text_position(
            wrapped_text, font, bbox, settings
        )
        
        # Рисуем текст
        draw = ImageDraw.Draw(image)
        
        # Рисуем обводку если нужна
        if settings['stroke_width'] > 0:
            self._draw_text_with_stroke(
                draw, text_x, text_y, wrapped_text, font, 
                settings['font_color'], settings['stroke_color'], settings['stroke_width']
            )
        else:
            # Обычный текст
            draw.multiline_text(
                (text_x, text_y), wrapped_text, 
                font=font, fill=settings['font_color'],
                align=settings['alignment']
            )
        
        return image
    
    def _calculate_optimal_font_size(self, 
                                   text: str, 
                                   width: int, 
                                   height: int, 
                                   settings: Dict[str, Any]) -> int:
        """Автоматический расчет оптимального размера шрифта"""
        
        # Начинаем с разумного размера
        min_size = 8
        max_size = min(width // 2, height // 2, 48)  # Ограничиваем максимум
        
        if max_size < min_size:
            return min_size
        
        best_size = min_size
        padding = settings['padding']
        
        # Бинарный поиск оптимального размера
        for font_size in range(min_size, max_size + 1, 2):
            font = self._get_font(settings['font_family'], font_size)
            wrapped_text = self._wrap_text(text, font, width - padding * 2)
            
            # Проверяем, помещается ли текст
            bbox = self._get_text_bbox(wrapped_text, font)
            if bbox[2] <= width - padding * 2 and bbox[3] <= height - padding * 2:
                best_size = font_size
            else:
                break
        
        logger.info(f"📏 Автоматический размер шрифта: {best_size}px для области {width}x{height}")
        return best_size
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
        """Перенос текста по словам"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Пробуем добавить слово к текущей строке
            test_line = current_line + [word]
            test_text = ' '.join(test_line)
            
            bbox = font.getbbox(test_text)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line = test_line
            else:
                # Слово не помещается, начинаем новую строку
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Даже одно слово не помещается - принудительно добавляем
                    lines.append(word)
        
        # Добавляем последнюю строку
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _calculate_text_position(self, 
                               text: str, 
                               font: ImageFont.ImageFont, 
                               bbox: List[int], 
                               settings: Dict[str, Any]) -> Tuple[int, int]:
        """Расчет позиции текста в области"""
        
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        padding = settings['padding']
        alignment = settings['alignment']
        
        # Получаем размеры текста
        text_bbox = self._get_text_bbox(text, font)
        text_width = text_bbox[2]
        text_height = text_bbox[3]
        
        # Вертикальное центрирование
        text_y = y1 + (height - text_height) // 2
        
        # Горизонтальное выравнивание
        if alignment == 'center':
            text_x = x1 + (width - text_width) // 2
        elif alignment == 'right':
            text_x = x2 - text_width - padding
        else:  # left
            text_x = x1 + padding
        
        # Ограничиваем позицию областью
        text_x = max(x1 + padding, min(text_x, x2 - text_width - padding))
        text_y = max(y1 + padding, min(text_y, y2 - text_height - padding))
        
        return text_x, text_y
    
    def _get_text_bbox(self, text: str, font: ImageFont.ImageFont) -> Tuple[int, int, int, int]:
        """Получение размеров текста"""
        lines = text.split('\n')
        max_width = 0
        total_height = 0
        
        for line in lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            
            max_width = max(max_width, line_width)
            total_height += line_height
        
        return (0, 0, max_width, total_height)
    
    def _get_font(self, font_family: str, font_size: int) -> ImageFont.ImageFont:
        """Получение шрифта с кэшированием"""
        
        cache_key = f"{font_family}_{font_size}"
        if cache_key in self.fonts_cache:
            return self.fonts_cache[cache_key]
        
        try:
            # Пытаемся загрузить системный шрифт
            if font_family.lower() == 'arial':
                # Разные пути для разных ОС
                font_paths = [
                    "/System/Library/Fonts/Arial.ttf",  # macOS
                    "C:/Windows/Fonts/arial.ttf",       # Windows
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux альтернатива
                ]
                
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, font_size)
                        break
                else:
                    # Fallback на дефолтный шрифт
                    font = ImageFont.load_default()
            else:
                # Попытка загрузить другой шрифт
                font = ImageFont.truetype(font_family, font_size)
                
        except (IOError, OSError):
            # Fallback на дефолтный шрифт
            logger.warning(f"⚠️ Не удалось загрузить шрифт {font_family}, используем default")
            font = ImageFont.load_default()
        
        self.fonts_cache[cache_key] = font
        return font
    
    def _draw_text_with_stroke(self, 
                              draw: ImageDraw.ImageDraw, 
                              x: int, y: int, 
                              text: str, 
                              font: ImageFont.ImageFont, 
                              fill_color: Tuple[int, int, int], 
                              stroke_color: Tuple[int, int, int], 
                              stroke_width: int):
        """Рисование текста с обводкой"""
        
        # Рисуем обводку (сдвигаем текст во все стороны)
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:  # Не рисуем в центре
                    draw.multiline_text(
                        (x + dx, y + dy), text, 
                        font=font, fill=stroke_color
                    )
        
        # Рисуем основной текст поверх
        draw.multiline_text((x, y), text, font=font, fill=fill_color)

    def preview_settings(self, 
                        image_path: str, 
                        sample_bbox: List[int], 
                        sample_text: str, 
                        settings: Dict[str, Any]) -> np.ndarray:
        """
        Предварительный просмотр настроек на небольшой области
        
        Args:
            image_path: путь к изображению
            sample_bbox: область для превью
            sample_text: пример текста
            settings: настройки форматирования
            
        Returns:
            Изображение-превью
        """
        image = Image.open(image_path).convert('RGB')
        
        # Создаем фейковый результат для превью
        fake_result = {
            'bbox': sample_bbox,
            'translated_text': sample_text
        }
        
        # Обрабатываем только эту область
        processed = self._process_text_region(image, fake_result, settings)
        
        # Возвращаем только обработанную область для превью
        x1, y1, x2, y2 = sample_bbox
        cropped = processed.crop((
            max(0, x1 - 20), max(0, y1 - 20),
            min(processed.width, x2 + 20), min(processed.height, y2 + 20)
        ))
        
        return np.array(cropped)