# GPU Setup Instructions

## Требования для другого ПК

### Обязательные требования:
- **NVIDIA GPU** с поддержкой CUDA 12.x
- **CUDA Toolkit 12.4** (или совместимая версия)
- **Python 3.10+**
- **Node.js 20.x**
- **Windows 10/11** (или Linux с поддержкой CUDA)

### Проверка GPU на другом ПК:
```bash
nvidia-smi
```
Должна отобразиться информация о GPU и версии CUDA.

## Установка на другом ПК

### 1. Установка Python-зависимостей с GPU поддержкой

```bash
# Активируйте виртуальное окружение
venv\Scripts\activate

# Установите GPU-версии пакетов
pip install -r requirements.txt
```

**Важно:** requirements.txt теперь содержит:
- `onnxruntime-gpu==1.20.1` - GPU-ускорение для InsightFace
- `faiss-gpu==1.8.0` - GPU-ускорение для FAISS индекса

### 2. Если возникнут ошибки при установке

#### Ошибка onnxruntime-gpu:
```bash
# Сначала установите CUDA Toolkit 12.4 с сайта NVIDIA
# Затем попробуйте альтернативную версию:
pip install onnxruntime-gpu==1.17.1
```

#### Ошибка faiss-gpu:
```bash
# Убедитесь что CUDA Toolkit установлен
# Попробуйте conda-установку:
conda install -c pytorch -c nvidia faiss-gpu=1.8.0
```

### 3. Кэширование моделей InsightFace

Перед первым запуском скачайте модель buffalo_l:

```bash
python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', root='models', providers=['CUDAExecutionProvider', 'CPUExecutionProvider']).prepare(ctx_id=0, det_size=(640,640))"
```

### 4. Запуск проекта

```bash
npm run dev
```

## Проверка GPU-ускорения

### 1. Проверка InsightFace GPU
При запуске `face_server.py` в логах должно быть:
```
[FaceEngine] INFO: NVIDIA GPU detected. Using CUDA.
[FaceEngine] INFO: InsightFace loaded on CUDAExecutionProvider.
```

### 2. Проверка FAISS GPU
В логах должно быть:
```
[FaceEngine] INFO: FAISS GPU support initialized successfully.
[FaceEngine] INFO: FAISS using GPU index.
```

### 3. Проверка через API
```bash
curl http://localhost:8001/status
```

Ответ должен содержать:
```json
{
  "provider": "CUDAExecutionProvider",
  "faiss_vectors": 123,
  ...
}
```

## Fallback на CPU

Если GPU недоступен, система автоматически переключится на CPU:

### InsightFace fallback:
```
[FaceEngine] WARNING: No GPU providers found. Falling back to CPU.
[FaceEngine] INFO: InsightFace loaded on CPU.
```

### FAISS fallback:
```
[FaceEngine] WARNING: FAISS GPU initialization failed: ...
[FaceEngine] INFO: FAISS will use CPU fallback.
[FaceEngine] INFO: FAISS using CPU index.
```

## Ожидаемое ускорение

### С GPU по сравнению с CPU:
- **Детекция лиц**: 3-5x быстрее
- **Распознавание**: 3-5x быстрее
- **Поиск по FAISS**: 5-10x быстрее
- **Общая производительность**: 2-3x для real-time системы

## Troubleshooting

### Ошибка: CUDA not available
```bash
# Проверьте установку CUDA
nvidia-smi

# Проверьте переменные окружения
echo %CUDA_PATH%
```

### Ошибка: cuDNN not found
Установите cuDNN для вашей версии CUDA с сайта NVIDIA.

### Ошибка: Out of memory
Уменьшите `det_size` в face_server.py или используйте меньшую модель buffalo_s вместо buffalo_l.

### Если GPU не работает вообще
Установите CPU-версии:
```bash
pip install onnxruntime==1.20.1 faiss-cpu==1.8.0.post1
```

## Мониторинг производительности

Используйте `nvidia-smi` для мониторинга GPU:
```bash
nvidia-smi -l 1  # Обновление каждую секунду
```

## Контакты для поддержки

Если возникнут проблемы:
1. Проверьте логи в `logs/face_server.log`
2. Проверьте compatibility CUDA Toolkit vs onnxruntime-gpu
3. Попробуйте fallback на CPU версии
