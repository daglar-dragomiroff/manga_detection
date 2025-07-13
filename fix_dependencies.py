# fix_dependencies.py - Скрипт автоматического исправления проблем
import subprocess
import sys
import os

def run_command(command, description):
    """Выполнение команды с логированием"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            return True
        else:
            print(f"❌ {description} - ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False

def fix_googletrans_conflict():
    """Исправление конфликта с googletrans"""
    print("🚀 Устранение конфликта зависимостей...")
    
    commands = [
        ("pip uninstall googletrans -y", "Удаление googletrans"),
        ("pip uninstall httpx -y", "Удаление старого httpx"),
        ("pip install httpx>=0.28.0", "Установка нового httpx"),
        ("pip install deep-translator>=1.11.4", "Установка deep-translator"),
    ]
    
    for command, description in commands:
        run_command(command, description)

def install_tesseract_languages():
    """Установка языковых пакетов Tesseract"""
    print("🌍 Установка языковых пакетов Tesseract...")
    
    # Определяем ОС
    if sys.platform.startswith('linux'):
        commands = [
            ("sudo apt-get update", "Обновление пакетов"),
            ("sudo apt-get install -y tesseract-ocr", "Установка Tesseract"),
            ("sudo apt-get install -y tesseract-ocr-jpn", "Японский язык"),
            ("sudo apt-get install -y tesseract-ocr-kor", "Корейский язык"),
            ("sudo apt-get install -y tesseract-ocr-chi-sim", "Китайский язык"),
            ("sudo apt-get install -y tesseract-ocr-rus", "Русский язык"),
        ]
        
        for command, description in commands:
            run_command(command, description)
            
    elif sys.platform == 'darwin':  # macOS
        commands = [
            ("brew install tesseract", "Установка Tesseract"),
            ("brew install tesseract-lang", "Установка языковых пакетов"),
        ]
        
        for command, description in commands:
            run_command(command, description)
            
    else:  # Windows
        print("🪟 Для Windows:")
        print("1. Скачайте Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Установите в C:\\Program Files\\Tesseract-OCR\\")
        print("3. Добавьте в PATH: C:\\Program Files\\Tesseract-OCR\\")

def reinstall_ocr_packages():
    """Переустановка OCR пакетов"""
    print("📦 Переустановка OCR пакетов...")
    
    commands = [
        ("pip uninstall paddlepaddle paddleocr -y", "Удаление старых версий"),
        ("pip install paddlepaddle>=3.0.0", "Установка PaddlePaddle"),
        ("pip install paddleocr>=3.1.0", "Установка PaddleOCR"),
        ("pip install easyocr>=1.7.0", "Установка EasyOCR"),
        ("pip install pytesseract>=0.3.10", "Установка PyTesseract"),
    ]
    
    for command, description in commands:
        run_command(command, description)

def main():
    """Основная функция исправления"""
    print("🛠️  Автоматическое исправление зависимостей манга-переводчика\n")
    
    # Меню выбора
    print("Выберите действие:")
    print("1. Исправить конфликт googletrans/httpx")
    print("2. Установить языковые пакеты Tesseract")
    print("3. Переустановить OCR пакеты")
    print("4. Выполнить все исправления")
    print("0. Выход")
    
    try:
        choice = input("\nВведите номер (0-4): ").strip()
        
        if choice == '1':
            fix_googletrans_conflict()
        elif choice == '2':
            install_tesseract_languages()
        elif choice == '3':
            reinstall_ocr_packages()
        elif choice == '4':
            fix_googletrans_conflict()
            print("\n" + "="*50)
            install_tesseract_languages()
            print("\n" + "="*50)
            reinstall_ocr_packages()
        elif choice == '0':
            print("👋 До свидания!")
            return
        else:
            print("❌ Неверный выбор")
            return
            
        print("\n🎉 Исправления завершены!")
        print("💡 Запустите: python setup_check.py для проверки")
        
    except KeyboardInterrupt:
        print("\n👋 Отменено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()