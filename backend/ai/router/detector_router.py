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
    Выбирает детектор на основе камеры/зоны/сценария.
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

    async def get(self, camera=None, scenario=None, zone=None):
        """
        Получить подходящий детектор

        Args:
            camera: Объект камеры (для чтения настроек)
            scenario: Сценарий (Entrance, Checkpoint, Parking, Street, Office, Lobby, Elevator, Corridor)
            zone: Зона внутри камеры (для разных зон разные детекторы)

        Returns:
            Инстанс детектора
        """
        ai_manager = self._get_ai_manager()
        if not ai_manager:
            return None

        # 1. Zone-level detector override
        if zone and isinstance(zone, dict):
            zone_detector = zone.get('detector')
            if zone_detector:
                detector = await ai_manager.get_detector(zone_detector)
                if detector:
                    return detector

        # 2. Camera-level detector override
        if camera and isinstance(camera, dict):
            camera_detector = camera.get('default_detector') or camera.get('detector_profile')
            if camera_detector:
                detector = await ai_manager.get_detector(camera_detector)
                if detector:
                    return detector

        # 3. Scenario-based routing
        if scenario:
            scenario_map = {
                'Street': 'retinaface',
                'Parking': 'retinaface',
                'Corridor': 'yoloface',
                'Entrance': 'scrfd',
                'Lobby': 'scrfd',
                'Office': 'scrfd',
                'Elevator': 'scrfd',
                'Checkpoint': 'scrfd',
            }
            detector_name = scenario_map.get(scenario, 'scrfd')
            if detector_name != 'scrfd':
                detector = await ai_manager.get_detector(detector_name)
                if detector:
                    return detector

        # 4. Fallback to AIManager default detector
        if ai_manager._active_detector_name:
            detector = await ai_manager.get_detector(ai_manager._active_detector_name)
            if detector:
                return detector

        # 5. Final fallback
        detector = await ai_manager.get_detector('scrfd')
        if detector:
            return detector

        # 6. Ultimate fallback
        return None
