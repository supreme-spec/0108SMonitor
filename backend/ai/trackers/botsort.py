"""
BoT-SORT - трекинг лиц

Пока не реализован.
"""

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo


class BoTSORT(BaseModule):
    """
    BoT-SORT - улучшенный трекинг с SDE
    
    Пока не реализован.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info = ModuleInfo(
            name="BoT-SORT",
            type=ModuleType.TRACKER,
            version="0.1",
            provider="CPU",
            enabled=False,
            status=ModuleStatus.NOT_INSTALLED,
            description="Улучшенный трекинг с SDE",
            priority=4
        )

    async def initialize(self) -> bool:
        """Инициализация BoT-SORT"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def load_models(self) -> bool:
        """Загрузка моделей BoT-SORT"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def unload_models(self) -> bool:
        """Выгрузка моделей BoT-SORT"""
        self.status = ModuleStatus.INSTALLED
        return True
