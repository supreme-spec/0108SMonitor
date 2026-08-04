# Archive Batch Processor

Модуль для пакетной обработки архивных фото и зачисления персонала.

## Структура

```
backend/archive/
├── __init__.py          # Экспорты модулей
├── config.py            # Конфигурация и профили
├── processor.py         # Основной процессор архива
├── quality.py           # Оценка качества лиц
├── cluster.py           # Кластеризация лиц по идентичности
├── intake.py            # Intake pipeline для персонала
├── profile_classifier.py # Авто-определение источника
└── ocr.py               # Извлечение OSD текста
```

## Модули

### config.py
- Пути к библиотекам AI из `D:\AI_Libraries`
- Конфигурация профилей обработки (modern_1080p, color_lowres, ir_screen_photo)
- Настройка порогов по умолчанию

### processor.py
- `ArchiveProcessor.process_folder()` - обработка папки с фото
- Авто-определение профиля источника
- Детекция лиц с SCRFD
- Извлечение эмбеддингов
- Кластеризация по людям

### quality.py
- `calculate_composite_quality()` - комплексная оценка качества
- Метрики: размытие, яркость, поза, окклюзия
- Тиры: A (хорошо), B (удовлетворительно), C (плохо), D (очень плохо)

### cluster.py
- `GreedyClusterer` - жадная кластеризация по порогу
- `deduplicate_faces()` - удаление дубликатов
- `merge_clusters_by_similarity()` - слияние похожих кластеров

### intake.py
- `PersonIntakePipeline.process_folder()` - обработка папки персонала
- Quality-гейт (только тир A/B)
- Дедупликация по косинусу
- Diversity-отбор (8 лучших фото)
- Генерация ч/б-близнецов

### profile_classifier.py
- `classify_source_profile()` - авто-определение типа источника
- Признаки: разрешение, цвет, OSD, муар

### ocr.py
- `extract_osd_text()` - извлечение текста OSD
- `extract_timestamp()` - парсинг даты/времени
- `extract_camera_id()` - извлечение ID камеры

## Профили обработки

### modern_1080p
- Современные камеры 1080p+
- SCRFD + ArcFace
- Авто-матч тира A

### color_lowres
- Старые цветные камеры
- SCRFD+RetinaFace ансамбль
- Строгие пороги

### ir_screen_photo
- ИК/пересъёмки с монитора
- AdaFace для низкого качества
- Модельное качество

## Использование

```python
from backend.archive import ArchiveProcessor, PersonIntakePipeline

# Обработка архива
processor = ArchiveProcessor(profile="auto")
result = processor.process_folder("path/to/folder")

# Зачисление персонала
pipeline = PersonIntakePipeline()
report = pipeline.process_folder("path/to/person/photos", "John Doe")
```

## Prisma Models

См. `prisma/schema.prisma`:
- `Episode` - папка с фото
- `EpisodePerson` - связь между эпизодом и персоной
- `ArchivePhoto` - архивное фото
- `ArchiveFace` - детектированное лицо
- `FaceCluster` - кластер лиц
- `PersonPolicy` - контекстные роли
