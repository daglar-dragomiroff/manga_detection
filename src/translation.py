# src/translation.py - Исправленный переводчик
from deep_translator import GoogleTranslator
from typing import Optional

class TextTranslator:
    def __init__(self):
        """Инициализация переводчика"""
        # Маппинг кодов языков для корректной работы с deep-translator
        self.language_mapping = {
            'zh': 'zh-cn',  # КИТАЙСКИЙ: zh → zh-cn (ИСПРАВЛЕНИЕ!)
            'ja': 'ja',     # японский остается как есть
            'ko': 'ko',     # корейский остается как есть
            'en': 'en',     # английский остается как есть
            'ru': 'ru'      # русский остается как есть
        }
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Перевод текста с исправленным маппингом для китайского языка
        
        Args:
            text: текст для перевода
            source_lang: исходный язык (zh, ja, ko, en, ru)
            target_lang: целевой язык (zh, ja, ko, en, ru)
            
        Returns:
            Переведенный текст
        """
        if not text or not text.strip():
            return ""
        
        # Если языки одинаковые - не переводим
        if source_lang == target_lang:
            return text
        
        # Применяем маппинг кодов языков
        mapped_source = self.language_mapping.get(source_lang, source_lang)
        mapped_target = self.language_mapping.get(target_lang, target_lang)
        
        # Отладочная информация (можно убрать после исправления)
        print(f"🌐 Перевод: {source_lang}({mapped_source}) → {target_lang}({mapped_target})")
        print(f"📝 Текст: '{text}'")
        
        try:
            translator = GoogleTranslator(
                source=mapped_source,
                target=mapped_target
            )
            result = translator.translate(text)
            
            if result and result != text:
                print(f"✅ Переведено: '{result}'")
                return result
            else:
                print(f"⚠️ Перевод не изменился")
                return text
                
        except Exception as e:
            print(f"❌ Ошибка перевода: {e}")
            # Если основной метод не работает, пробуем альтернативный
            return self._translate_alternative(text, source_lang, target_lang)
    
    def _translate_alternative(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Альтернативный метод перевода с проверкой разных вариантов китайского
        """
        print("🔄 Пробуем альтернативный метод перевода...")
        
        # Для китайского языка пробуем разные варианты кодов
        if source_lang == 'zh':
            chinese_variants = ['zh-cn', 'zh', 'chinese (simplified)', 'chinese']
            
            for variant in chinese_variants:
                try:
                    print(f"🔄 Пробуем код китайского: '{variant}'")
                    translator = GoogleTranslator(source=variant, target=target_lang)
                    result = translator.translate(text)
                    
                    if result and result != text:
                        print(f"✅ Успешно с кодом '{variant}': '{result}'")
                        return result
                        
                except Exception as e:
                    print(f"❌ Код '{variant}' не сработал: {e}")
                    continue
            
            print(f"⚠️ Все варианты китайского не сработали, возвращаем оригинал")
            return text
        
        # Для других языков пробуем стандартный подход
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            return result if result else text
        except Exception as e:
            print(f"❌ Альтернативный метод тоже не сработал: {e}")
            return text