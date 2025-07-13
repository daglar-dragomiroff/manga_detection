# Автоматический переводчик манги

Приложение для автоматического перевода японской, корейской и китайской манги с использованием нейронных сетей.

## 🚀 Быстрый старт

### 1. Устранение конфликтов зависимостей

Если у вас установлен `googletrans`, удалите его (конфликтует с новыми версиями httpx):

```bash
pip uninstall googletrans -y
```

### 2. Чистая установка

```bash
# Создайте новое виртуальное окружение
python -m venv manga_env
source manga_env/bin/activate  # Linux/macOS
# или
manga_env\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Установите Tesseract OCR (системная зависимость)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-kor tesseract-ocr-chi-sim

# macOS:
brew install tesseract tesseract-lang

# Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki
```

### 3. Проверка системы

```bash
python setup_check.py
```

### 4. Запуск

```bash
streamlit run app.py
```

## 📋 Описание

Проект реализует полный пайплайн обработки страниц манги:
- **Детекция речевых пузырей** с помощью YOLOv8
- **Множественное OCR** (PaddleOCR, EasyOCR, Tesseract) для максимальной точности
- **Автоматический перевод** на множество языков
- **Веб-интерфейс** для удобной работы с результатами

## 🛠 Технологии

- **Детекция объектов**: YOLOv8 (Ultralytics)
- **OCR системы**: 
  - PaddleOCR (лучший для азиатских языков)
  - EasyOCR (универсальный)
  - Tesseract (резервный)
- **Перевод**: Google Translate API через deep-translator
- **Интерфейс**: Streamlit
- **Обработка изображений**: OpenCV, Pillow

## 🌍 Поддерживаемые языки

### Распознавание (OCR):
- 🇯🇵 Японский (хирагана, катакана, кандзи)
- 🇰🇷 Корейский (хангыль)
- 🇨🇳 Китайский (упрощенный и традиционный)
- 🇬🇧 Английский
- 🇷🇺 Русский

### Перевод:
- Любые языки, поддерживаемые Google Translate

## ⚡ Производительность

- **Детекция пузырей**: ~100-500ms на изображение
- **OCR на пузырь**: ~200-800ms (зависит от размера и сложности)
- **Перевод**: ~100-300ms на фразу

**Общее время**: 2-15 секунд на страницу (зависит от количества текста)

## 🔧 Решение проблем

### Ошибка "googletrans requires httpx==0.13.3"

```bash
pip uninstall googletrans -y
pip install deep-translator
```

### PaddleOCR не установился

```bash
# Для CPU (рекомендовано)
pip install paddlepaddle
pip install paddleocr

# Для GPU (если есть CUDA)
pip install paddlepaddle-gpu
pip install paddleocr
```

### Tesseract не найден

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-kor tesseract-ocr-chi-sim tesseract-ocr-rus
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
1. Скачайте установщик: https://github.com/UB-Mannheim/tesseract/wiki
2. Установите в C:\Program Files\Tesseract-OCR\
3. Добавьте в PATH: C:\Program Files\Tesseract-OCR\

### EasyOCR долго загружается

При первом запуске EasyOCR скачивает модели (~100-500MB). Это нормально.

### Модель детекции не найдена

Убедитесь, что файл `manga_bubble_detector_best.pt` находится в папке `models/`.

### Низкое качество OCR

1. Попробуйте другой порог уверенности детекции
2. Проверьте качество исходного изображения
3. Убедитесь, что выбран правильный язык

## 📁 Структура проекта

```
manga_detection/
├── models/                    # Обученные модели
│   └── manga_bubble_detector_best.pt
├── src/                      # Исходный код
│   ├── detection.py          # Детекция пузырей
│   ├── ocr.py               # OCR системы  
│   ├── translation.py       # Перевод
│   └── utils.py             # Утилиты
├── data/                    # Данные
│   ├── uploads/             # Загруженные файлы
│   └── outputs/             # Результаты
├── static/                  # Статические файлы
├── app.py                   # Главное приложение
├── config.py                # Конфигурация
├── setup_check.py           # Проверка системы
├── requirements.txt         # Зависимости
└── README.md               # Документация
```

## 🎯 Использование

1. **Запустите приложение**: `streamlit run app.py`
2. **Откройте в браузере**: http://localhost:8501
3. **Загрузите изображение** страницы манги
4. **Выберите языки** (исходный и целевой)
5. **Настройте параметры** детекции
6. **Нажмите "Начать обработку"**
7. **Просмотрите и отредактируйте** результаты
8. **Сохраните** готовый перевод

## 🏗 Архитектура OCR

Система использует каскадный подход:

1. **Предобработка изображения**:
   - Увеличение контраста
   - Шумоподавление  
   - Масштабирование маленьких областей

2. **Множественное распознавание**:
   - PaddleOCR (приоритет для азиатских языков)
   - EasyOCR (универсальное решение)
   - Tesseract (резервный вариант)

3. **Выбор лучшего результата** по алгоритму:
   - Приоритет движка
   - Длина распознанного текста
   - Уверенность распознавания

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для фичи: `git checkout -b feature/amazing-feature`
3. Коммитьте изменения: `git commit -m 'Add amazing feature'`
4. Push в ветку: `git push origin feature/amazing-feature`
5. Создайте Pull Request

## 📝 Лицензия

Разработано в рамках курса машинного обучения.

## 🆘 Поддержка

Если возникли проблемы:

1. Запустите `python setup_check.py` для диагностики
2. Проверьте системные требования
3. Убедитесь в корректности установки зависимостей
4. Создайте Issue с описанием проблемы

## 🔮 Планы развития

- [ ] Поддержка batch-обработки
- [ ] Интеграция inpainting моделей для лучшего замещения текста
- [ ] API для интеграции с другими приложениями
- [ ] Поддержка больше форматов файлов
- [ ] Улучшение точности детекции для сложных случаев