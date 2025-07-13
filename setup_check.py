# setup_check.py - Скрипт проверки системы
import sys
import subprocess
import importlib.util

def check_package(package_name, import_name=None):
    """Проверка установки пакета"""
    if import_name is None:
        import_name = package_name
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            print(f"✅ {package_name} установлен")
            return True
        else:
            print(f"❌ {package_name} не найден")
            return False
    except ImportError:
        print(f"❌ {package_name} не удалось импортировать")
        return False

def check_tesseract():
    """Проверка Tesseract OCR"""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract версия {version} установлен")
        return True
    except Exception as e:
        print(f"❌ Tesseract не найден: {e}")
        print("💡 Установите Tesseract:")
        print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-kor")
        print("   macOS: brew install tesseract tesseract-lang")
        print("   Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def fix_googletrans_conflict():
    """Исправление конфликта googletrans с httpx"""
    print("\n🔧 Исправление конфликта googletrans...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "googletrans", "-y"], 
                      capture_output=True)
        print("✅ googletrans удален (конфликтовал с httpx)")
        print("ℹ️  Используется deep-translator вместо googletrans")
        return True
    except Exception as e:
        print(f"⚠️  Не удалось удалить googletrans: {e}")
        return False

def main():
    print("🚀 Проверка системы переводчика манги\n")
    
    # Основные библиотеки
    packages = [
        ("streamlit", "streamlit"),
        ("torch", "torch"),
        ("ultralytics", "ultralytics"),
        ("opencv-python", "cv2"),
        ("Pillow", "PIL"),
        ("numpy", "numpy"),
    ]
    
    print("📦 Основные библиотеки:")
    for package, import_name in packages:
        check_package(package, import_name)
    
    print("\n🔤 OCR библиотеки:")
    ocr_packages = [
        ("paddlepaddle", "paddle"),
        ("paddleocr", "paddleocr"),
        ("easyocr", "easyocr"),
        ("pytesseract", "pytesseract"),
    ]
    
    for package, import_name in ocr_packages:
        check_package(package, import_name)
    
    print("\n🧪 Tesseract OCR:")
    check_tesseract()
    
    print("\n🌐 Переводчик:")
    check_package("deep-translator", "deep_translator")
    
    print("\n🔧 Проверка конфликтов:")
    try:
        import googletrans
        print("⚠️  googletrans найден - может конфликтовать с httpx")
        fix_googletrans_conflict()
    except ImportError:
        print("✅ googletrans не установлен (хорошо)")
    
    # Проверка модели детекции
    print("\n🎯 Модель детекции:")
    import os
    model_path = "models/manga_bubble_detector_best.pt"
    if os.path.exists(model_path):
        print(f"✅ Модель найдена: {model_path}")
    else:
        print(f"❌ Модель не найдена: {model_path}")
        print("💡 Скачайте модель и поместите в папку models/")
    
    print("\n🎉 Проверка завершена!")
    print("💡 Запустите: streamlit run app.py")

if __name__ == "__main__":
    main()