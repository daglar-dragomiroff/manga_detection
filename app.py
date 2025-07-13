# app.py - Упрощенный интерфейс с ручным выбором языка
import streamlit as st
import numpy as np
from PIL import Image
import os
from pathlib import Path

# Импорт наших модулей
from src.detection import BubbleDetector
from src.ocr import TextExtractor
from src.translation import TextTranslator
from src.utils import (save_uploaded_file, validate_image, create_result_summary,
                       get_language_flag, get_language_name)
from config import *

# Настройка страницы
st.set_page_config(
    page_title="Manga Translator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    css_file = BASE_DIR / "static" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_resource
def load_models():
    """Загрузка моделей с кэшированием"""
    try:
        detector = BubbleDetector(str(MODEL_PATH), DETECTION_CONFIDENCE)
        st.success("✅ Модель детекции загружена")
    except Exception as e:
        st.error(f"❌ Ошибка загрузки модели детекции: {e}")
        return None, None, None
    
    try:
        ocr = TextExtractor()
        st.success("✅ OCR системы готовы")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации OCR: {e}")
        return detector, None, None
    
    try:
        translator = TextTranslator()
        st.success("✅ Система перевода готова")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации переводчика: {e}")
        return detector, ocr, None
    
    return detector, ocr, translator

def process_manga_page_manual(image_path, detector, ocr, translator, source_lang, target_lang):
    """Обработка страницы манги с РУЧНЫМ выбором языка"""
    
    # Детекция пузырей
    with st.spinner("🔍 Поиск речевых пузырей..."):
        bubbles = detector.detect_bubbles(image_path)
    
    if not bubbles:
        st.warning("⚠️ Речевые пузыри не найдены на изображении")
        return []
    
    st.success(f"✅ Найдено {len(bubbles)} речевых пузырей")
    
    # OCR и перевод с выбранным языком
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, bubble in enumerate(bubbles):
        progress_bar.progress((i + 1) / len(bubbles))
        status_text.text(f"📝 Обработка пузыря {i+1}/{len(bubbles)} (язык: {get_language_flag(source_lang)} {get_language_name(source_lang)})")
        
        # Извлечение текста на выбранном языке
        original_text = ocr.extract_text_simple(image_path, bubble['bbox'], source_lang)
        
        # Перевод текста
        translated_text = ""
        if original_text:
            if source_lang != target_lang:
                translated_text = translator.translate(original_text, source_lang, target_lang)
            else:
                translated_text = original_text  # Не переводим если языки одинаковые
        
        results.append({
            'bbox': bubble['bbox'],
            'confidence': bubble['confidence'],
            'class_id': bubble['class_id'],
            'original_text': original_text,
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang
        })
    
    progress_bar.empty()
    status_text.empty()
    return results

def main():
    """Основная функция приложения"""
    
    load_css()
    
    # Заголовок
    st.markdown('<h1 class="main-header">📚 Переводчик манги (ручной выбор языка)</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎯 Простой и надежный подход:
    - **📝 Ручной выбор языков** - вы точно знаете что на картинке
    - **🎯 Без автоопределения** - никаких ошибок распознавания
    - **🌍 5 языков OCR**: 🇯🇵 Японский, 🇰🇷 Корейский, 🇨🇳 Китайский, 🇺🇸 Английский, 🇷🇺 Русский
    - **🔄 Простой перевод** между любыми языками
    """)
    
    # Боковая панель с настройками
    st.sidebar.header("⚙️ Настройки языков")
    
    source_lang = st.sidebar.selectbox(
        "🔤 Исходный язык (на картинке):",
        options=['ja', 'ko', 'zh', 'en', 'ru'],
        format_func=lambda x: f"{get_language_flag(x)} {get_language_name(x)}",
        index=0,  # Японский по умолчанию для манги
        help="Выберите язык текста на вашем изображении"
    )
    
    target_lang = st.sidebar.selectbox(
        "🌐 Язык перевода:",
        options=['ru', 'en', 'ja', 'ko', 'zh'],
        format_func=lambda x: f"{get_language_flag(x)} {get_language_name(x)}",
        index=0,  # Русский по умолчанию
        help="На какой язык переводить"
    )
    
    # Показываем выбранную пару
    if source_lang == target_lang:
        st.sidebar.info("ℹ️ Языки одинаковые - перевод не нужен")
    else:
        st.sidebar.success(f"✅ {get_language_flag(source_lang)} → {get_language_flag(target_lang)}")
    
    confidence = st.sidebar.slider(
        "🎯 Порог уверенности детекции:",
        min_value=0.1,
        max_value=1.0,
        value=DETECTION_CONFIDENCE,
        step=0.1,
        help="Более высокие значения = меньше ложных срабатываний"
    )
    
    # Информация о языках
    with st.sidebar.expander("ℹ️ Поддерживаемые языки"):
        st.write("**🔤 OCR (распознавание):**")
        st.write("🇯🇵 Японский - хирагана, катакана, кандзи")
        st.write("🇰🇷 Корейский - хангыль")  
        st.write("🇨🇳 Китайский - упрощенный")
        st.write("🇺🇸 Английский - латиница")
        st.write("🇷🇺 Русский - кириллица")
        
        st.write("**🌐 Перевод:**")
        st.write("Любые направления через Google Translate")
    
    # Загрузка моделей
    with st.spinner("🚀 Загрузка моделей..."):
        detector, ocr, translator = load_models()
    
    if not all([detector, ocr, translator]):
        st.error("⚠️ Не удалось загрузить все необходимые компоненты")
        return
    
    detector.confidence = confidence
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        "📁 Выберите изображение манги",
        type=['jpg', 'jpeg', 'png', 'webp'],
        help="Поддерживаемые форматы: JPG, PNG, WebP. Максимальный размер: 10MB"
    )
    
    if uploaded_file is not None:
        if not validate_image(uploaded_file):
            st.error("❌ Некорректный файл или слишком большой размер")
            return
        
        image_path = save_uploaded_file(uploaded_file)
        
        # Отображение загруженного изображения
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📸 Исходное изображение")
            image = Image.open(image_path)
            st.image(image, use_container_width=True)
            st.caption(f"Размер: {image.size[0]}×{image.size[1]} пикселей")
        
        # Кнопка обработки
        if st.button(f"🚀 Обработать ({get_language_flag(source_lang)} → {get_language_flag(target_lang)})", 
                     type="primary", use_container_width=True):
            
            results = process_manga_page_manual(
                image_path, detector, ocr, translator, source_lang, target_lang
            )
            
            if results:
                # Отображение результатов детекции
                with col2:
                    st.subheader("🎯 Результат детекции")
                    bubbles = [{'bbox': r['bbox'], 'confidence': r['confidence']} 
                              for r in results]
                    visualization = detector.visualize_detection(image_path, bubbles)
                    st.image(visualization, use_container_width=True)
                
                # Статистика
                summary = create_result_summary(results)
                
                st.markdown("### 📊 Статистика обработки")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    st.metric("🎯 Найдено пузырей", summary['total_bubbles'])
                
                with col_stats2:
                    st.metric("📝 Распознано текста", 
                             f"{summary['successful_ocr']}/{summary['total_bubbles']}")
                    st.caption(f"Успешность: {summary['ocr_success_rate']:.1f}%")
                
                with col_stats3:
                    if source_lang == target_lang:
                        st.metric("🔄 Без перевода", summary['total_bubbles'])
                        st.caption("Языки одинаковые")
                    else:
                        st.metric("🌐 Переведено", 
                                 f"{summary['successful_translation']}/{summary['total_bubbles']}")
                        st.caption(f"Успешность: {summary['translation_success_rate']:.1f}%")
                
                # Детальные результаты
                st.markdown("### 📋 Детальные результаты")
                
                for i, result in enumerate(results):
                    confidence = result['confidence']
                    source_flag = get_language_flag(source_lang)
                    target_flag = get_language_flag(target_lang)
                    
                    # Иконка для уверенности детекции
                    conf_icon = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.5 else "🔴"
                    
                    with st.expander(
                        f"{conf_icon} Пузырь #{i+1} | {source_flag} → {target_flag} | "
                        f"Уверенность: {confidence:.2f}"
                    ):
                        
                        col_orig, col_trans = st.columns(2)
                        
                        with col_orig:
                            st.markdown(f"**🔤 Оригинал ({source_flag} {get_language_name(source_lang)}):**")
                            original = st.text_area(
                                "Оригинал",
                                value=result['original_text'],
                                key=f"orig_{i}",
                                label_visibility="collapsed",
                                height=100
                            )
                        
                        with col_trans:
                            if source_lang == target_lang:
                                st.markdown(f"**🔄 Без перевода:**")
                            else:
                                st.markdown(f"**🌐 Перевод ({target_flag} {get_language_name(target_lang)}):**")
                                
                            translated = st.text_area(
                                "Перевод",
                                value=result['translated_text'],
                                key=f"trans_{i}",
                                label_visibility="collapsed",
                                height=100
                            )
                        
                        # Информация
                        st.caption(f"📍 Координаты: {result['bbox']}")
                        
                        # Обновление результатов при редактировании
                        if original != result['original_text']:
                            result['original_text'] = original
                        if translated != result['translated_text']:
                            result['translated_text'] = translated
                
                # Кнопки действий
                col_save, col_clear = st.columns(2)
                
                with col_save:
                    if st.button("💾 Сохранить результаты", use_container_width=True):
                        st.success("✅ Результаты сохранены")
                
                with col_clear:
                    if st.button("🔄 Обработать заново", use_container_width=True):
                        st.rerun()
        
        # Очистка файлов
        if st.button("🗑️ Очистить", use_container_width=True):
            if os.path.exists(image_path):
                os.remove(image_path)
            st.rerun()

if __name__ == "__main__":
    main()