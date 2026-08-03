"""
ByteTrack - трекинг лиц

Пока не реализован.
"""

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo


class ByteTrack(BaseModule):
    """
    ByteTrack - быстрый трекинг с Kalman фильтром
    
    Пока не реализован.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info = ModuleInfo(
            name="ByteTrack",
            type=ModuleType.TRACKER,
            version="0.1",
            provider="CPU",
            enabled=False,
            status=ModuleStatus.NOT_INSTALLED,
            description="Быстрый трекинг с Kalman фильтром",
            priority=4
        )

    async def initialize(self) -> bool:
        """Инициализация ByteTrack"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def load_models(self) -> bool:
        """Загрузка моделей ByteTrack"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def unload_models(self) -> bool:
        """Выгрузка моделей ByteTrack"""
        self.status = ModuleStatus.INSTALLED
        return True
