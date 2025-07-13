import os
from pathlib import Path

# Пути к файлам и папкам
BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "models" / "manga_bubble_detector_best.pt"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

# Параметры модели детекции
DETECTION_CONFIDENCE = 0.5
IMAGE_SIZE = 640

# Параметры OCR - расширенная поддержка языков
SUPPORTED_LANGUAGES = {
    'ja': 'Японский',
    'ko': 'Корейский',
    'zh': 'Китайский',
    'en': 'Английский',
    'ru': 'Русский'
}
DEFAULT_SOURCE_LANG = 'ja'
DEFAULT_TARGET_LANG = 'ru'

# OCR настройки
OCR_ENGINES = {
    'paddle': True,    # Использовать PaddleOCR (лучший для азиатских языков)
    'easyocr': True,   # Использовать EasyOCR (универсальный)
    'tesseract': True  # Использовать Tesseract (резервный)
}

# Параметры предобработки изображений
IMAGE_PROCESSING = {
    'min_width': 10,      # Минимальная ширина области для OCR
    'min_height': 10,     # Минимальная высота области для OCR
    'upscale_threshold': 50,  # Увеличивать изображения меньше этого размера
    'contrast_factor': 1.5,   # Множитель контраста
    'sharpness_factor': 1.2,  # Множитель резкости
}

# Параметры качества OCR
OCR_QUALITY = {
    'min_confidence': 0.5,    # Минимальная уверенность для принятия результата
    'paddle_confidence': 0.5,  # Уверенность для PaddleOCR
    'easyocr_confidence': 0.5, # Уверенность для EasyOCR
    'tesseract_confidence': 0.3, # Уверенность для Tesseract (обычно ниже)
}

# ====== НОВЫЕ НАСТРОЙКИ ДЛЯ ФОРМАТИРОВАНИЯ ТЕКСТА ======

# Параметры заливки и форматирования текста
TEXT_FORMATTING = {
    'font_families': ['arial', 'times', 'courier', 'helvetica'],
    'font_sizes': list(range(8, 72, 2)),  # 8, 10, 12, ... 70
    'default_font_family': 'arial',
    'default_font_size': 16,
    'min_font_size': 8,
    'max_font_size': 48,
}

# Предустановленные цвета
PRESET_COLORS = {
    'Черный': (0, 0, 0),
    'Белый': (255, 255, 255),
    'Красный': (255, 0, 0),
    'Синий': (0, 0, 255),
    'Зеленый': (0, 128, 0),
    'Желтый': (255, 255, 0),
    'Фиолетовый': (128, 0, 128),
    'Серый': (128, 128, 128),
}

# Настройки заливки по умолчанию
DEFAULT_TEXT_SETTINGS = {
    'font_family': 'arial',
    'font_size': 16,
    'font_color': (0, 0, 0),      # Черный текст
    'bg_color': (255, 255, 255),  # Белый фон
    'stroke_width': 0,            # Толщина обводки
    'stroke_color': (0, 0, 0),    # Цвет обводки
    'padding': 5,                 # Отступы
    'alignment': 'center',        # Выравнивание (left, center, right)
    'transparency': 1.0,          # Прозрачность фона (0.0-1.0)
    'auto_font_size': True,       # Автоматический размер шрифта
    'enable_inpainting': True,    # Включить заливку
}

# Варианты выравнивания
TEXT_ALIGNMENTS = {
    'Слева': 'left',
    'По центру': 'center', 
    'Справа': 'right'
}

# ====== КОНЕЦ НОВЫХ НАСТРОЕК ======

# Параметры интерфейса
MAX_UPLOAD_SIZE = 10  # MB
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

# Создание необходимых папок
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Проверка доступности OCR движков
def check_ocr_availability():
    """Проверка доступности OCR движков"""
    available_engines = {}
    
    try:
        import paddleocr
        available_engines['paddle'] = True
    except ImportError:
        available_engines['paddle'] = False
    
    try:
        import easyocr
        available_engines['easyocr'] = True
    except ImportError:
        available_engines['easyocr'] = False
    
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        available_engines['tesseract'] = True
    except (ImportError, Exception):
        available_engines['tesseract'] = False
    
    return available_engines

# Утилиты для работы с цветами
def hex_to_rgb(hex_color: str) -> tuple:
    """Конвертация HEX в RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color: tuple) -> str:
    """Конвертация RGB в HEX"""
    return '#%02x%02x%02x' % rgb_color