# Calibration Module

Инструменты для настройки порогов распознавания под конкретные условия.

## benchmark_profiles.py

Калибровочный скрипт для анализа фото из разных источников.

### Использование

```bash
python calibration/benchmark_profiles.py D:\bd_gosti\test_dataset --models-root backend/ai/models
```

### Входные данные

Папка `test_dataset` должна содержать подпапки с фото разных типов:
- `modern_1080p/` - современные камеры 1080p+
- `color_lowres/` - старые цветные камеры низкого разрешения
- `ir_screen_photo/` - ИК/пересъёмки с монитора

### Выходные данные

Создаётся папка `calibration/out/` с файлами:
- `faces.csv` - метрики каждого лица (размер, качество, blur, brightness, color_vs_bw_self)
- `pairs.csv` - похожести между парами лиц (для определения T_INTRA)

### Формат faces.csv

```
folder,img,face,det_score,w,h,blur,brightness,color_vs_bw_self
modern_1080p,photo1.jpg,0,0.92,120,150,85.3,112.5,0.923
```

### Формат pairs.csv

```
folder,a,b,cos
modern_1080p,photo1.jpg#0,photo1.jpg#1,0.782
```

## Анализ результатов

### Определение границ тиров A/B/C/D

На основе `faces.csv`:
- **TIER A**: blur >= X, size >= Y, brightness в диапазоне
- **TIER B**: blur >= X-10, size >= Y-20
- **TIER C**: blur >= X-20, size >= Y-30
- **TIER D**: всё остальное

### Определение T_INTRA

На основе `pairs.csv` для одной и той же папки:
- Найти пары с одинаковыми именами (один человек)
- Найти пары с разными именами (разные люди)
- Найти оптимальный порог похожести

### Оценка дельты цвет-ч/б

Колонка `color_vs_bw_self` показывает похожесть цветного vs ч/б эмбеддингов:
- 0.85-0.95: хорошая корреляция
- 0.70-0.85: средняя (нужен ч/б-близнец)
- < 0.70: плохая (возможно ИК-камера)
