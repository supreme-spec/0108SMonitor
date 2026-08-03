"""
Router для детекторов

Выбирает детектор на основе сценария, зоны или качества изображения.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..base import ModuleStatus


class DetectorRouter:
    """
    Маршрутизатор детекторов
    Использует AIManager для получения активного детектора.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._current_detector = None
        self._ai_manager = None

    def _get_ai_manager(self):
        """Получить инстанс AIManager"""
        if self._ai_manager is None:
            try:
                from ..manager.ai_manager import AIManager
                self._ai_manager = AIManager.get_instance()
            except Exception as e:
                print(f"Failed to create AIManager: {e}")
        return self._ai_manager

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
        # Используем AIManager для получения активного детектора
        ai_manager = self._get_ai_manager()
        if ai_manager:
            return ai_manager._active_detector
        
        # Fallback: если AIManager недоступен, возвращаем None
        return None
