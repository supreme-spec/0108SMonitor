# Маршрутизатор модулей

Маршрутизация запросов между модулями:

- **ScenarioRouter** — выбор модуля по сценарию (Entrance, Checkpoint, Street и т.д.)
- **QualityRouter** — выбор модуля по качеству изображения
- **PriorityRouter** — выбор модуля по приоритету

## Сценарии

- **Entrance** — входные зоны (InsightFace + SCRFD)
- **Checkpoint** — турникеты (InsightFace + SCRFD)
- **Corridor** — коридоры (InsightFace + SCRFD)
- **Parking** — парковки (YOLO-Face или SCRFD)
- **Street** — улицы (RetinaFace или SCRFD)
- **Office** — офисы (InsightFace + SCRFD)
- **Lobby** — лобби (InsightFace + SCRFD)
- **Elevator** — лифты (InsightFace + SCRFD)

## Интерфейс BaseRouter

- `route(query)` — выбрать модули для запроса
- `get_detector(scenario)` — получить детектор по сценарию
- `get_recognizer(scenario)` — получить рекогнайзер по сценарию
