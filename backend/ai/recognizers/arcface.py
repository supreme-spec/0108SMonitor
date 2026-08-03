"""
ArcFace - распознавание лиц

ArcFace - это алгоритм распознавания лиц внутри фреймворка InsightFace.
Использует модель buffalo_l для извлечения эмбеддингов.
"""

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo
from typing import List


class ArcFace(BaseModule):
    """
    ArcFace - основной движок распознавания
    
    Использует модель buffalo_l для извлечения эмбеддингов.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info = ModuleInfo(
            name="ArcFace",
            type=ModuleType.RECOGNIZER,
            version="0.7.3",
            provider="CUDA",
            enabled=True,
            status=ModuleStatus.ACTIVE,
            description="Основной алгоритм распознавания лиц (buffalo_l)",
            priority=1,
            gpu_required=True,
            models=["buffalo_l"]
        )

    async def initialize(self) -> bool:
        """Инициализация ArcFace"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def load_models(self) -> bool:
        """Загрузка моделей ArcFace"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def unload_models(self) -> bool:
        """Выгрузка моделей ArcFace"""
        self.status = ModuleStatus.INSTALLED
        return True

    async def extract_embedding(self, image_bytes: bytes) -> List[float]:
        """Извлечь эмбеддинг из изображения"""
        # TODO: Реализовать через Python-сервер
        return [0.0] * 512
