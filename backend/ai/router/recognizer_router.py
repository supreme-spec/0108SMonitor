"""
Router для рекогнайзеров

Выбирает рекогнайзер на основе сценария и качества изображения.
"""

from ..recognizers.arcface import ArcFace
from ..recognizers.adaface import AdaFace


class RecognizerRouter:
    """
    Маршрутизатор рекогнайзеров
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._current_recognizer = None

    def get(self, camera=None, scenario=None, quality=None):
        """
        Получить подходящий рекогнайзер
        
        Args:
            camera: Объект камеры (для чтения настроек)
            scenario: Сценарий (Entrance, Checkpoint, Parking, Street, Office, Lobby, Elevator, Corridor)
            quality: Качество изображения (для выбора AdaFace при низком качестве)
            
        Returns:
            Инстанс рекогнайзера
        """
        # TODO: Реализовать логику выбора на основе config/ai_config.json
        # Пока возвращаем ArcFace как основной
        if self._current_recognizer is None:
            self._current_recognizer = ArcFace()
        
        return self._current_recognizer
