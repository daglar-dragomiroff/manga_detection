# app.py - Полнофункциональный интерфейс с заливкой и редактированием
import streamlit as st
import numpy as np
from PIL import Image
import os
import io
from pathlib import Path

# Импорт наших модулей
from src.detection import BubbleDetector
from src.ocr import TextExtractor
from src.translation import TextTranslator
from src.inpainting import TextInpainter  # НОВЫЙ МОДУЛЬ
from src.utils import (save_uploaded_file, validate_image, create_result_summary,
                       get_language_flag, get_language_name)
from config import *

# Настройка страницы
st.set_page_config(
    page_title="Manga Translator Pro",
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
        return None, None, None, None
    
    try:
        ocr = TextExtractor()
        st.success("✅ OCR системы готовы")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации OCR: {e}")
        return detector, None, None, None
    
    try:
        translator = TextTranslator()
        st.success("✅ Система перевода готова")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации переводчика: {e}")
        return detector, ocr, None, None
    
    try:
        inpainter = TextInpainter()  # НОВЫЙ КОМПОНЕНТ
        st.success("✅ Система заливки готова")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации заливки: {e}")
        return detector, ocr, translator, None
    
    return detector, ocr, translator, inpainter

def get_text_formatting_settings():
    """Получение настроек форматирования текста из интерфейса"""
    
    with st.sidebar.expander("🎨 Настройки форматирования", expanded=False):
        
        # Включить/выключить заливку
        enable_inpainting = st.checkbox(
            "🖌️ Включить заливку текста",
            value=DEFAULT_TEXT_SETTINGS['enable_inpainting'],
            help="Закрашивать исходный текст и вставлять перевод"
        )
        
        if not enable_inpainting:
            return None
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📝 Шрифт:**")
            
            font_family = st.selectbox(
                "Семейство:",
                options=TEXT_FORMATTING['font_families'],
                index=0,
                label_visibility="collapsed"
            )
            
            auto_font_size = st.checkbox(
                "Авто размер",
                value=DEFAULT_TEXT_SETTINGS['auto_font_size'],
                help="Автоматически подбирать размер шрифта"
            )
            
            if not auto_font_size:
                font_size = st.slider(
                    "Размер:",
                    min_value=TEXT_FORMATTING['min_font_size'],
                    max_value=TEXT_FORMATTING['max_font_size'],
                    value=DEFAULT_TEXT_SETTINGS['font_size'],
                    step=2,
                    label_visibility="collapsed"
                )
            else:
                font_size = DEFAULT_TEXT_SETTINGS['font_size']
            
            alignment = st.selectbox(
                "Выравнивание:",
                options=list(TEXT_ALIGNMENTS.keys()),
                index=1,  # По центру
                format_func=lambda x: x,
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("**🎨 Цвета:**")
            
            # Цвет текста
            font_color_preset = st.selectbox(
                "Цвет текста:",
                options=list(PRESET_COLORS.keys()),
                index=0,  # Черный
                label_visibility="collapsed"
            )
            
            # Цвет фона
            bg_color_preset = st.selectbox(
                "Цвет фона:",
                options=list(PRESET_COLORS.keys()),
                index=1,  # Белый
                label_visibility="collapsed"
            )
            
            transparency = st.slider(
                "Прозрачность фона:",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_TEXT_SETTINGS['transparency'],
                step=0.1,
                label_visibility="collapsed"
            )
        
        # Дополнительные настройки
        with st.expander("⚙️ Дополнительно"):
            stroke_width = st.slider(
                "Толщина обводки:",
                min_value=0,
                max_value=5,
                value=DEFAULT_TEXT_SETTINGS['stroke_width']
            )
            
            if stroke_width > 0:
                stroke_color_preset = st.selectbox(
                    "Цвет обводки:",
                    options=list(PRESET_COLORS.keys()),
                    index=0  # Черный
                )
            else:
                stroke_color_preset = 'Черный'
            
            padding = st.slider(
                "Отступы:",
                min_value=0,
                max_value=20,
                value=DEFAULT_TEXT_SETTINGS['padding']
            )
        
        # Формируем настройки
        settings = {
            'font_family': font_family,
            'font_size': font_size,
            'font_color': PRESET_COLORS[font_color_preset],
            'bg_color': PRESET_COLORS[bg_color_preset],
            'stroke_width': stroke_width,
            'stroke_color': PRESET_COLORS[stroke_color_preset],
            'padding': padding,
            'alignment': TEXT_ALIGNMENTS[alignment],
            'transparency': transparency,
            'auto_font_size': auto_font_size,
            'enable_inpainting': True,
        }
        
        return settings

def process_manga_page_with_inpainting(image_path, detector, ocr, translator, inpainter, 
                                     source_lang, target_lang, text_settings=None):
    """Обработка страницы манги С заливкой текста"""
    
    # Детекция пузырей
    with st.spinner("🔍 Поиск речевых пузырей..."):
        bubbles = detector.detect_bubbles(image_path)
    
    if not bubbles:
        st.warning("⚠️ Речевые пузыри не найдены на изображении")
        return [], None
    
    st.success(f"✅ Найдено {len(bubbles)} речевых пузырей")
    
    # OCR и перевод
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
    
    # НОВАЯ ЧАСТЬ: Создаем финальное изображение с заливкой
    final_image = None
    if text_settings and text_settings.get('enable_inpainting', False):
        with st.spinner("🎨 Создание финального изображения с заливкой..."):
            try:
                final_image = inpainter.inpaint_and_replace_text(
                    image_path, results, text_settings
                )
                st.success("✅ Заливка текста выполнена")
            except Exception as e:
                st.error(f"❌ Ошибка заливки: {e}")
                final_image = None
    
    return results, final_image

def create_download_link(image_array, filename="translated_manga.png"):
    """Создание ссылки для скачивания изображения"""
    
    # Конвертируем numpy array в изображение
    image = Image.fromarray(image_array.astype('uint8'), 'RGB')
    
    # Сохраняем в байтовый буфер
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_data = img_buffer.getvalue()
    
    # Создаем кнопку скачивания
    st.download_button(
        label="💾 Скачать переведенную мангу",
        data=img_data,
        file_name=filename,
        mime="image/png",
        use_container_width=True
    )

def main():
    """Основная функция приложения"""
    
    load_css()
    
    # Заголовок
    st.markdown('<h1 class="main-header">📚 Переводчик манги Pro (с заливкой)</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎯 Полнофункциональный переводчик:
    - **📝 Ручной выбор языков** - точность распознавания
    - **🎨 Умная заливка** - закрашивание + вставка перевода  
    - **🎨 Форматирование текста** - шрифт, цвет, размер, обводка
    - **💾 Сохранение результата** - готовая переведенная манга
    - **🌍 5 языков OCR**: 🇯🇵 Японский, 🇰🇷 Корейский, 🇨🇳 Китайский, 🇺🇸 Английский, 🇷🇺 Русский
    """)
    
    # Боковая панель с настройками
    st.sidebar.header("⚙️ Настройки")
    
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
    
    # НОВАЯ ЧАСТЬ: Настройки форматирования
    text_settings = get_text_formatting_settings()
    
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
        detector, ocr, translator, inpainter = load_models()
    
    if not all([detector, ocr, translator, inpainter]):
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
        
        # Отображение исходного изображения
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📸 Исходное изображение")
            image = Image.open(image_path)
            st.image(image, use_container_width=True)
            st.caption(f"Размер: {image.size[0]}×{image.size[1]} пикселей")
        
        # Кнопка обработки
        process_button_text = "🚀 Обработать"
        if text_settings and text_settings.get('enable_inpainting'):
            process_button_text += " + Заливка"
        else:
            process_button_text += " (без заливки)"
        
        process_button_text += f" ({get_language_flag(source_lang)} → {get_language_flag(target_lang)})"
        
        if st.button(process_button_text, type="primary", use_container_width=True):
            
            results, final_image = process_manga_page_with_inpainting(
                image_path, detector, ocr, translator, inpainter, 
                source_lang, target_lang, text_settings
            )
            
            if results:
                # ИСПРАВЛЕННАЯ ЧАСТЬ: Показываем И детекцию И заливку
                with col2:
                    # ВСЕГДА показываем детекцию
                    st.subheader("🎯 Результат детекции")
                    bubbles = [{'bbox': r['bbox'], 'confidence': r['confidence']} 
                              for r in results]
                    visualization = detector.visualize_detection(image_path, bubbles)
                    st.image(visualization, use_container_width=True)
                    
                    # ДОПОЛНИТЕЛЬНО показываем заливку если она есть
                    if final_image is not None:
                        st.subheader("🎨 Результат с заливкой")
                        st.image(final_image, use_container_width=True)
                        
                        # Кнопка скачивания
                        create_download_link(final_image, f"translated_{uploaded_file.name}")
                
                # Сохраняем результаты в session state для редактирования
                st.session_state['results'] = results
                st.session_state['image_path'] = image_path
                st.session_state['text_settings'] = text_settings
                
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
                
                # НОВАЯ ЧАСТЬ: Детальные результаты с возможностью редактирования
                st.markdown("### 📋 Редактирование результатов")
                
                # Флаг изменений
                changes_made = False
                
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
                        
                        # Проверяем изменения
                        if original != result['original_text']:
                            result['original_text'] = original
                            changes_made = True
                        if translated != result['translated_text']:
                            result['translated_text'] = translated
                            changes_made = True
                
                # Кнопка пересоздания изображения после редактирования
                if changes_made and text_settings and text_settings.get('enable_inpainting'):
                    if st.button("🔄 Пересоздать изображение с изменениями", 
                                use_container_width=True, type="secondary"):
                        
                        with st.spinner("🎨 Пересоздание изображения..."):
                            try:
                                updated_image = inpainter.inpaint_and_replace_text(
                                    image_path, results, text_settings
                                )
                                
                                st.success("✅ Изображение обновлено!")
                                
                                # Показываем обновленное изображение
                                st.subheader("🆕 Обновленный результат")
                                st.image(updated_image, use_container_width=True)
                                
                                # Новая кнопка скачивания
                                create_download_link(updated_image, f"updated_{uploaded_file.name}")
                                
                            except Exception as e:
                                st.error(f"❌ Ошибка обновления: {e}")
        
        # Очистка файлов
        if st.button("🗑️ Очистить", use_container_width=True):
            if os.path.exists(image_path):
                os.remove(image_path)
            # Очищаем session state
            for key in ['results', 'image_path', 'text_settings']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()