"""
Router для детекторов

Выбирает детектор на основе сценария, зоны или качества изображения.
"""

from ..detectors.scrfd import SCRFD
from ..detectors.yoloface import YOLOFace
from ..detectors.retinaface import RetinaFace


class DetectorRouter:
    """
    Маршрутизатор детекторов
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._current_detector = None

    def get(self, camera=None, scenario=None, zone=None):
        """
        Получить подходящий детектор
        
        Args:
            camera: Объект камеры (для чтения настроек)
            scenario: Сценарий (Entrance, Checkpoint, Parking, Street, Office, Lobby, Elevator, Corridor)
            zone: Зона внутри камеры (для разных зон разные детекторы)
            
        Returns:
            Инстанс детектора
        """
        # TODO: Реализовать логику выбора на основе config/ai_config.json
        # Пока возвращаем SCRFD как основной
        if self._current_detector is None:
            self._current_detector = SCRFD()
        
        return self._current_detector
