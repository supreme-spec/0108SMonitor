# Multi-Module Recognition System

## Обзор

Система теперь поддерживает три модуля распознавания:
- **Face Recognition** - распознавание лиц (InsightFace + FAISS)
- **Motion Detection** - детекция движения (OpenCV MOG2)
- **LPR** - распознавание номерных знаков (EasyOCR)

## Архитектура

```
Camera → Module Selector → Specific Module Server → Results → Database
```

## Модули

### 1. Face Recognition (уже работает)
- **Сервер:** `face_server.py` (порт 8001)
- **Технологии:** InsightFace buffalo_l + FAISS
- **Использование:** Входные зоны, турникеты
- **Точность:** 98%+ при хорошем качестве

### 2. Motion Detection (новый)
- **Сервер:** `motion_server.py` (порт 8002)
- **Технологии:** OpenCV MOG2 background subtraction
- **Использование:** Периметр, коридоры, склады
- **Настройки:** Порог чувствительности, зоны детекции

### 3. LPR (новый)
- **Сервер:** `lpr_server.py` (порт 8003)
- **Технологии:** EasyOCR + контурный анализ
- **Использование:** Парковки, КПП
- **Регионы:** RU, EU, US, CN, KZ, BY, UA

## Конфигурация камеры

Каждая камера может иметь включённые модули:

```json
{
  "enabled_modules": ["face", "motion", "lpr"],
  "motion_threshold": 0.62,
  "motion_zones": [...],
  "lpr_regions": ["RU", "EU"]
}
```

## API Endpoints

### Module Management

```bash
# Получить модули камеры
GET /api/cameras/:id/modules

# Обновить модули камеры
PATCH /api/cameras/:id/modules
Body: { "enabled_modules": ["face", "motion"] }

# Обновить порог движения
PATCH /api/cameras/:id/motion-threshold
Body: { "motion_threshold": 0.7 }

# Обновить регионы LPR
PATCH /api/cameras/:id/lpr-regions
Body: { "lpr_regions": ["RU", "EU"] }
```

### Module Servers

#### Motion Server (8002)
```bash
GET /health
GET /status
POST /camera/:id/init
POST /camera/:id/zones
POST /camera/:id/process
DELETE /camera/:id
```

#### LPR Server (8003)
```bash
GET /health
GET /status
POST /regions
POST /process
```

## Интеграция в UI

### React Component
- `ModuleSelector.tsx` - компонент выбора модулей
- Интегрирован в страницу камер (`Cameras.tsx`)
- Показывает активные модули и настройки

### Функции:
- Включение/выключение модулей
- Настройка порога движения
- Выбор регионов для LPR
- Визуальный статус модулей

## Запуск модулей

### Development
```bash
# Все модули вместе
npm run dev

# Отдельно
npm run dev:face     # Face Recognition (8001)
python motion_server.py  # Motion Detection (8002)
python lpr_server.py     # LPR (8003)
```

### Production
```bash
# Face Recognition
nohup python face_server.py > logs/face.log 2>&1 &

# Motion Detection
nohup python motion_server.py > logs/motion.log 2>&1 &

# LPR
nohup python lpr_server.py > logs/lpr.log 2>&1 &
```

## Рекомендации по использованию

### Face Recognition
- Входные зоны, турникеты
- Хорошее освещение
- Камеры лицом к людям
- Разрешение минимум 1080p

### Motion Detection
- Периметр здания
- Коридоры и проходы
- Складские помещения
- Ночные зоны с ИК-подсветкой

### LPR
- Парковки
- КПП и въездные ворота
- Улицы перед зданием
- Камеры под углом 45° к номерам

## Производительность

### GPU-ускорение
- Face Recognition: 3-5x быстрее с GPU
- Motion Detection: CPU достаточно
- LPR: GPU улучшает точность

### Ресурсы
- Face: ~2GB VRAM, ~30% CPU
- Motion: ~5% CPU
- LPR: ~1GB VRAM, ~15% CPU

## Troubleshooting

### Motion Detection не работает
- Проверьте порог чувствительности
- Убедитесь что зоны настроены корректно
- Проверьте освещение в зоне

### LPR не распознаёт
- Установите EasyOCR: `pip install easyocr`
- Проверьте разрешение камеры (минимум 720p)
- Убедитесь что номера видны четко

### Face Recognition медленно
- Проверьте GPU-ускорение
- Уменьшите det_size в face_server.py
- Уменьшите количество активных камер

## Будущие улучшения

1. **Deep Learning Motion** - YOLO для детекции движения
2. **Advanced LPR** - специализированные модели для каждого региона
3. **Module Priority** - приоритизация модулей при ограниченных ресурсах
4. **Smart Load Balancing** - автоматическое распределение нагрузки между GPU/CPU
