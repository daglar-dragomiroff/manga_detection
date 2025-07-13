# src/utils.py - Упрощенные утилиты
import os
import uuid
from PIL import Image
import streamlit as st
from typing import List, Dict, Any

def save_uploaded_file(uploaded_file) -> str:
    """Сохранение загруженного файла"""
    file_extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    
    from config import UPLOAD_DIR
    filepath = UPLOAD_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(filepath)

def validate_image(file) -> bool:
    """Проверка корректности изображения"""
    from config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
    
    _, ext = os.path.splitext(file.name)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return False
    
    if file.size > MAX_UPLOAD_SIZE * 1024 * 1024:
        return False
    
    return True

def create_result_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Создание простой сводки результатов"""
    total_bubbles = len(results)
    successful_ocr = sum(1 for r in results if r.get('original_text', '').strip())
    successful_translation = sum(1 for r in results if r.get('translated_text', '').strip())
    
    return {
        'total_bubbles': total_bubbles,
        'successful_ocr': successful_ocr,
        'successful_translation': successful_translation,
        'ocr_success_rate': (successful_ocr / total_bubbles * 100) if total_bubbles > 0 else 0,
        'translation_success_rate': (successful_translation / total_bubbles * 100) if total_bubbles > 0 else 0
    }

def get_language_flag(lang_code: str) -> str:
    """Получение флага для языка"""
    flags = {
        'ja': '🇯🇵',
        'ko': '🇰🇷', 
        'zh': '🇨🇳',
        'en': '🇺🇸',
        'ru': '🇷🇺'
    }
    return flags.get(lang_code, '❓')

def get_language_name(lang_code: str) -> str:
    """Получение названия языка"""
    names = {
        'ja': 'Японский',
        'ko': 'Корейский', 
        'zh': 'Китайский',
        'en': 'Английский',
        'ru': 'Русский'
    }
    return names.get(lang_code, 'Неизвестный')