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
        # 1. Zone-level detector override
        if zone and isinstance(zone, dict):
            zone_detector = zone.get('detector')
            if zone_detector:
                ai_manager = self._get_ai_manager()
                if ai_manager and zone_detector != ai_manager._config_data.get('active', {}).get('detector'):
                    try:
                        import asyncio
                        loop = asyncio.get_running_loop()
                        if loop.is_running():
                            # We cannot block the event loop; caller must switch detector explicitly
                            pass
                    except Exception:
                        pass
                return self._resolve_detector(zone_detector)

        # 2. Camera-level detector override
        if camera and isinstance(camera, dict):
            camera_detector = camera.get('default_detector') or camera.get('detector_profile')
            if camera_detector:
                return self._resolve_detector(camera_detector)

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
                return self._resolve_detector(detector_name)

        # 4. Fallback to AIManager active detector
        ai_manager = self._get_ai_manager()
        if ai_manager and ai_manager._active_detector:
            return ai_manager._active_detector

        # 5. Final fallback
        return self._resolve_detector('scrfd')

    def _resolve_detector(self, name: str):
        """Resolve detector by name, loading via AIManager if needed."""
        ai_manager = self._get_ai_manager()
        if ai_manager is None:
            return None
        try:
            import asyncio
            current = ai_manager._config_data.get('active', {}).get('detector') if ai_manager._config_data else None
            if name != current:
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        # Schedule switch but don't await; next detect may use previous until ready
                        loop.create_task(ai_manager.switch_detector_async(name))
                except RuntimeError:
                    # No running loop
                    asyncio.run(ai_manager.switch_detector_async(name))
        except Exception:
            pass
        return ai_manager._active_detector
