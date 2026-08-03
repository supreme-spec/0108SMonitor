"""
Router для трекеров

Выбирает трекер на основе сценария и требований к производительности.
"""

from ..trackers.bytetrack import ByteTrack
from ..trackers.botsort import BoTSORT


class TrackerRouter:
    """
    Маршрутизатор трекеров
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._current_tracker = None

    def get(self, camera=None, scenario=None):
        """
        Получить подходящий трекер
        
        Args:
            camera: Объект камеры (для чтения настроек)
            scenario: Сценарий (Entrance, Checkpoint, Parking, Street, Office, Lobby, Elevator, Corridor)
            
        Returns:
            Инстанс трекера
        """
        # TODO: Реализовать логику выбора на основе config/ai_config.json
        # Пока возвращаем ByteTrack как основной
        if self._current_tracker is None:
            self._current_tracker = ByteTrack()
        
        return self._current_tracker
