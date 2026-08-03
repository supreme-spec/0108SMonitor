# AUDIT_CURRENT_ARCHITECTURE.md

## 1. Поток камеры

### Назначение
Получение видеопотока с RTSP-камеры и детекция лиц на каждом кадре.

### Где находится
```
server.ts
startCameraPipeline()
startCameraDetection()
```

### Жизненный цикл
```
RTSP
  ↓
FFmpeg (декодирование MJPEG)
  ↓
cameraFrames (буфер кадров Map<number, {frame, faces}>)
  ↓
startCameraDetection() - каждые 500мс
  ↓
detectFaces(buf) - детекция через Python face_server.py
  ↓
processDetectedFaces()
  ↓
SCRFD через /api/ai/detect
  ↓
enriched faces (с bbox, confidence, track_id)
```

### Входные данные
- `cam.source` - RTSP URL
- `cam.id` - идентификатор камеры
- `fallbackFrame` - бэкап-кадр

### Выходные данные
- `cameraFrames.set(cam.id, {frame: base64, faces: enriched[]})`
- `enriched[i]` содержит: `bbox`, `confidence`, `track_id`, `person_id`, `person_name`, `category`

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| Frame | FFmpeg | startCameraPipeline | stopCameraPipeline |
| CameraFrames | startCameraPipeline | detectionTimer | stopCameraPipeline |
| Face Detection | detectFaces() | detectFaces() | GC |

### Точки расширения
- Можно добавить `track_id` в enriched faces (уже есть `track_id: i+1`)
- Можно вставить FaceQuality между detectFaces и processDetectedFaces
- Можно добавить кэширование детекции для пропуска повторных вызовов

## 2. Smart Capture

### Назначение
Запись короткого видео (клипа) при срабатывании события, если включена умная запись.

### Где находится
```
server.ts
triggerSmartRecording()
startFileRecording()
```

### Жизненный цикл
```
Событие (RECOGNIZED / UNKNOWN / CONFIRMATION)
  ↓
triggerSmartRecording(cam)
  ↓
if cam.is_smart_recording AND !activeRecordings.has(cam.id)
  ↓
startFileRecording(cam, 15) - запись 15 секунд
  ↓
ffmpeg записывает в recordings/camXXX_timestamp.mp4
  ↓
создаётся Recording в БД
  ↓
activeRecordings.delete(cam.id) при завершении
```

### Входные данные
- `cam.is_smart_recording` - флаг включения
- `activeRecordings` - проверка, что не идёт уже запись

### Выходные данные
- Видеофайл: `recordings/cam{cam.id}_{timestamp}.mp4`
- БД запись: `Recording` (camera_id, video_path, duration, size_mb)

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| Recording | startFileRecording | finish handler | никогда |
| activeRecordings | startFileRecording | close handler | close handler |

### Точки расширения
- **Можно расширить**: добавить буфер кадров в памяти (не писать сразу на диск)
- **Можно расширить**: добавить `track_id` в Recording
- **Можно расширить**: добавить `best_frame` (лучший кадр из записанного)
- **Можно расширить**: добавить фильтрацию по качеству лица перед записью

### Проблема
Сейчас Smart Capture **пишет сразу на диск** через ffmpeg. Нет буфера кадров в памяти.
Для вставки FaceQuality нужно переработать архитектуру.

## 3. Фотохроника (Chronicle)

### Назначение
Архив событий с фотографиями по камерам и датам.

### Где находится
```
server.ts
recordVisitor()
chronicleData Map<number, Map<string, Visitor[]>>
```

### Жизненный цикл
```
Событие (RECOGNIZED / UNKNOWN / CONFIRMATION)
  ↓
saveSnapshotFromFrame()
  ↓
recordVisitor(cameraId, person_id, person_name, snapshot_path)
  ↓
chronicleData[cameraId][date].unshift(visitor)
```

### Входные данные
- `cameraId`
- `person_id` (может быть null для неизвестного)
- `person_name`
- `snapshot_path`

### Выходные данные
- `Visitor` объект с полями: `filename`, `person_id`, `person_name`, `time`, `photo_url`, `size_kb`

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| Chronicle Entry | recordVisitor | никогда | архив (ручное удаление) |

### Точки расширения
- **Можно расширить**: добавить `track_id`
- **Можно расширить**: добавить `quality_score`
- **Можно расширить**: добавить `best_frame`
- **Можно расширить**: добавить `embedding_id`

### БД связь
Фотохроника — **in-memory структура**, не связана напрямую с БД.
В БД есть таблица `Event` с `snapshot_path`.

## 4. Incident

### Назначение
Запись инцидентов с привязкой к человеку.

### Где находится
```
prisma/schema.prisma
model Incident
```

### Жизненный цикл
```
Событие (RECOGNIZED / BLACKLIST_ALERT / VIP_ARRIVAL)
  ↓
persistAndBroadcastEvent()
  ↓
prisma.event.create() → Event таблица
```

### Входные данные
```
{
  cameraId,
  cameraName,
  personId,
  event_type,
  confidence,
  snapshot_path,
  person_name,
  person_category,
  person_photo_path,
  needs_operator_confirmation,
  confirmation_status
}
```

### Выходные данные
- БД запись: `Event` таблица
- WebSocket уведомление

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| Incident | persistAndBroadcastEvent | никогда | никогда (или вручную) |

### Точки расширения
- **Можно расширить**: добавить `track_id`
- **Можно расширить**: добавить `best_frame`
- **Можно расширить**: добавить `embedding`

### БД таблица Event
```
model Event {
  id
  camera_id
  camera_name
  person_id
  event_type
  confidence
  snapshot_path
  person_name
  person_category
  person_photo_path
  created_at
  needs_operator_confirmation
  confirmation_status
  confirmation_id
}
```

## 5. AIManager

### Назначение
Единая точка входа для AI операций (детекторы, рекогнайзеры, трекеры).

### Где находится
```
backend/ai/manager/ai_manager.py
class AIManager
```

### Жизненный цикл
```
Request /api/ai/detect
  ↓
AIManager.detect(image_bytes)
  ↓
_active_detector.detect_with_embedding()
  ↓
SCRFD / YOLO / RetinaFace через InsightFace
  ↓
return faces with bbox, det_score, kps, embedding
```

### Входные данные
- `image_bytes` - байты изображения

### Выходные данные
```
[
  {
    bbox: [x1, y1, x2, y2],
    det_score: float,
    kps: [[x,y], ...],
    embedding: [512 floats],
    age: int,
    gender: int
  }
]
```

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| Active Detector | _load_detector() | switch_detector_async() | unload_models() |
| Active Recognizer | _load_recognizer() | switch_recognizer_async() | unload_models() |
| Active Tracker | _load_tracker() | switch_tracker_async() | unload_models() |

### Точки расширения
- **Можно расширить**: добавить Quality этап
- **Можно расширить**: добавить Tracker в пайплайн detect()
- **Можно расширить**: добавить метод `detect_with_tracking()`

### Методы AIManager
| Метод | Поддержка |
|-------|-----------|
| switch_detector_async() | ✅ |
| switch_recognizer_async() | ✅ |
| switch_tracker_async() | ✅ |
| hot-swap без перезапуска | ✅ |

### Текущая проблема
`AIManager.detect()` вызывает детектор **без трекера**.
Нужен новый метод `AIManager.detect_track_quality()` для полного пайплайна.

## 6. Router

### Назначение
Маршрутизация запросов к активным модулям.

### Где находится
```
backend/ai/router/detector_router.py
backend/ai/router/recognizer_router.py
backend/ai/router/tracker_router.py
```

### Жизненный цикл
```
Request
  ↓
DetectorRouter
  ↓
_active_detector (SCRFD / YOLO / RetinaFace)
  ↓
response
```

### Входные данные
- `route` - путь запроса
- `request` - данные запроса

### Выходные данные
- Результат вызова активного модуля

### Владельцы объектов
| Объект | Создаёт | Изменяет | Удаляет |
|--------|---------|----------|---------|
| DetectorRouter | AIManager | AIManager | AIManager |
| RecognizerRouter | AIManager | AIManager | AIManager |
| TrackerRouter | AIManager | AIManager | AIManager |

### Точки расширения
- **Можно расширить**: добавить QualityRouter
- **Можно расширить**: добавить SelectorRouter

## 7. База данных

### Таблицы
```
Camera - конфигурация камер
Category - категории (BLACKLIST, VIP, STAFF, etc.)
Person - люди в базе
FaceDescriptor - эмбеддинги (person_id, descriptor)
PersonPhoto - фотографии людей
FaceConfirmation - подтверждения оператора
Event - события (распознавания, алерты)
Recording - видеозаписи
Incident - инциденты
Tag - теги людей
Settings - настройки
FaissUpdateLog - логи обновлений FAISS
```

### Точки расширения
- **Можно расширить**: добавить поле `track_id` в Event
- **Можно расширить**: добавить поле `best_frame` в Event
- **Можно расширить**: добавить таблицу `TrackSnapshot` (для хранения лучших кадров треков)
- **Можно расширить**: добавить поле `quality_score` в PersonPhoto

## 8. Отсутствующие компоненты

### FaceQuality
❌ Не существует - **нужно создать**

### BestFrameSelector
❌ Не существует - **нужно создать**

### EmbeddingManager
❌ Не существует - **нужно создать**

### ByteTrack
❌ Не существует (только заготовка) - **нужно создать**

### TrackCandidate
❌ Не существует - **нужно создать**

## 9. ЖИЗНЕННЫЙ ЦИКЛ ОДНОГО ЧЕЛОВЕКА

```
RTSP
  ↓
FFmpeg (декодирование MJPEG)
  ↓
cameraFrames (буфер кадров)
  ↓
detectionTimer (500ms)
  ↓
detectFaces(buf) →SCRFD→
  ↓
faces (bbox, det_score, kps, embedding)
  ↓
processDetectedFaces()
  ↓
searchByDescriptor(desc, lowT) → FAISS
  ↓
match? → RECOGNIZED / UNKNOWN
  ↓
persistAndBroadcastEvent() → Event таблица
  ↓
saveSnapshotFromFrame() → snapshot_path
  ↓
recordVisitor() → chronicleData
  ↓
triggerSmartRecording() → Recording (если включено)
```

**Проблема**: Нет трекинга (`track_id = i+1` только для порядка обработки).
Нет накопления кадров для выбора лучшего.
Нет оценки качества перед выбором лучшего кадра.

## 10. ПЛАН МИНИМАЛЬНЫХ ИЗМЕНЕНИЙ

| Элемент | Действие | Приоритет |
|---------|----------|-----------|
| Camera | оставить | - |
| Zone (из schema) | расширить (добавить type: PASSAGE/CHECKPOINT/QUEUE/DOOR/TURNSTILE) | medium |
| Event | расширить (добавить track_id, best_frame, quality_score) | high |
| Incident | оставить (использовать Event как инцидент) | - |
| AIManager | расширить (добавить пайплайн Detector→Tracker→Quality→Recognizer) | high |
| Router | расширить (добавить QualityRouter, SelectorRouter) | medium |
| Smart Capture | переработать (добавить буфер кадров в памяти) | high |
| PhotoHistory | расширить (добавить track_id, best_frame) | medium |
| FaceQuality | создать | critical |
| BestFrameSelector | создать | critical |
| EmbeddingManager | создать | critical |
| ByteTrack | создать | critical |
| TrackCandidate | создать | critical |

## 11. ARCHITECTURE MAP

```
RTSP Camera
      │
      ▼
 CameraManager (server.ts)
      │
      ▼
 Frame (cameraFrames Map)
      │
      ▼
 Detector Router
      │
      ├──────────────► SCRFD / YOLO / Retina
      │                     │
      │                     ▼
      │                 detections (bbox, det_score, kps, embedding)
      │                     │
      │                     ▼
      │            Track Manager (TODO: ByteTrack)
      │                     │
      │                     ▼
      │            TrackCandidate (TODO: new class)
      │                     │
      │                     ▼
      │            FaceQuality (TODO: new class)
      │                     │
      │                     ▼
      │            BestFrameSelector (TODO: new class)
      │                     │
      ▼                     ▼
 Smart Capture (TODO: rewrite with buffer)
      │
      ├────────────────── PhotoHistory (chronicleData)
      │
      ▼
 Event (DB) → Incident
      │
      ▼
 ArcFace → FAISS
      │
      ▼
 EmbeddingManager (TODO: new class)
```

## 12. ОТВЕТ НА ГЛАВНЫЙ ВОПРОС

> **Можно ли реализовать архитектуру "Track → Best Frame → ArcFace → FAISS", изменив менее 20% существующего кода?**

### Ответ: **НЕТ**

### Причины:

1. **Smart Capture пишет сразу на диск** — нет буфера кадров в памяти для анализа качества и выбора лучшего.

2. **Нет кл��сса Track** — `track_id` сейчас просто `i+1` в цикле, не сохраняется между кадрами.

3. **Нет FaceQuality** — оценка качества лица есть в `face_server.py` как `/assess-quality` endpoint, но не используется в пайплайне.

4. **Нет BestFrameSelector** — нет модуля для выбора лучшего кадра из буфера.

5. **Нет TrackCandidate** — нет объекта для накопления кадров, метаданных, качества и эмбеддингов по треку.

6. **AIManager.detect() не использует трекер** — пайплайн не включает трекинг.

7. **Event таблица не хранит track_id** — нет связи между событием и треком.

### Что можно оставить без изменений:
- Camera — конфигурация
- Zone (из schema) — можно просто расширить типами
- Event — можно добавить новые поля
- FAISS — уже используется для поиска
- ArcFace — уже используется для распознавания

### Что нужно создать с нуля (новые классы):
- `TrackCandidate` — объект для одного прохода человека
- `FaceQuality` — оценка качества лица
- `BestFrameSelector` — выбор лучшего кадра
- `EmbeddingManager` — управление эмбеддингами
- `ByteTrack` — трекинг лиц по видеопотоку
- `VideoBuffer` — буфер кадров для Smart Capture

### Что нужно расширить (добавить методы/поля):
- `AIManager` — добавить метод `detect_track_quality()` для полного пайплайна
- `Event` — добавить поля `track_id`, `best_frame`, `quality_score`
- `Smart Capture` — добавить буфер кадров в памяти

### Вывод:
Для реализации полноценной архитектуры "Track → Best Frame → ArcFace → FAISS" нужно:
1. Создать 5 новых классов (TrackCandidate, FaceQuality, BestFrameSelector, EmbeddingManager, ByteTrack)
2. Расширить 3 существующих модуля (AIManager, Event, Smart Capture)
3. Изменить порядка **30-40%** существующего кода

**Рекомендация**: Делать поэтапно:
- Этап 1: ByteTrack → TrackCandidate → VideoBuffer
- Этап 2: FaceQuality → BestFrameSelector
- Этап 3: EmbeddingManager → ArcFace integration
- Этап 4: Integration в existing workflow (Event, Smart Capture)

Такой подход позволит сохранить рабочую систему на каждом этапе и избежать полной переработки.
