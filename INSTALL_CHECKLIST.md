# Installation Checklist for Another PC

## Перед установкой

- [ ] Скопировать весь проект `smart-security-monitor` на другой ПК
- [ ] Убедиться что на другом ПК есть NVIDIA GPU
- [ ] Проверить установлен ли CUDA Toolkit 12.x: `nvidia-smi`
- [ ] Если CUDA нет - установить с сайта NVIDIA

## Установка

### Python окружение
- [ ] Создать виртуальное окружение: `python -m venv venv`
- [ ] Активировать: `venv\Scripts\activate` (Windows)
- [ ] Установить зависимости: `pip install -r requirements.txt`
- [ ] Проверить GPU поддержку: `python check_gpu.py`

### Node.js окружение
- [ ] Установить Node.js зависимости: `npm install`
- [ ] Настроить базу данных: `npm run db:migrate`

### Модели InsightFace
- [ ] Скачать модель buffalo_l:
  ```bash
  python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', root='models', providers=['CUDAExecutionProvider', 'CPUExecutionProvider']).prepare(ctx_id=0, det_size=(640,640))"
  ```

### Настройка
- [ ] Скопировать `.env.example` в `.env`
- [ ] Проверить настройки в `.env`
- [ ] Убедиться что FFmpeg установлен (для камер)

## Тестирование

### Запуск
- [ ] Запустить проект: `npm run dev`
- [ ] Проверить что фронтенд доступен: http://localhost:5173
- [ ] Проверить что бэкенд доступен: http://localhost:3000
- [ ] Проверить что face server доступен: http://localhost:8001/health

### Проверка GPU
- [ ] Проверить логи face_server.py на наличие:
  - `[FaceEngine] INFO: NVIDIA GPU detected. Using CUDA.`
  - `[FaceEngine] INFO: FAISS GPU support initialized successfully.`
- [ ] Проверить статус через API: `curl http://localhost:8001/status`
- [ ] Убедиться что `"provider": "CUDAExecutionProvider"`

### Функциональное тестирование
- [ ] Добавить тестовую камеру
- [ ] Добавить тестовую персону с фото
- [ ] Проверить детекцию лиц
- [ ] Проверить распознавание лиц
- [ ] Проверить события в ленте

## Troubleshooting

Если что-то не работает:

### GPU не работает
- [ ] Проверить `nvidia-smi`
- [ ] Проверить логи в `logs/face_server.log`
- [ ] Попробовать CPU-версии: `pip install onnxruntime faiss-cpu`

### Модели не загружаются
- [ ] Проверить папку `models/`
- [ ] Проверить интернет-соединение
- [ ] Скачать модели вручную

### База данных
- [ ] Проверить файл `prisma/dev.db`
- [ ] Запустить `npm run db:migrate` снова

## Документация

- [ ] Прочитать `GPU_SETUP.md` для детальных инструкций
- [ ] Прочитать `README.md` для общей информации
- [ ] Проверить `SETUP.md` для базовой установки

## Завершение

- [ ] Система работает стабильно
- [ ] GPU ускорение активно (если доступно)
- [ ] Все основные функции протестированы
- [ ] Логи чистые без ошибок
