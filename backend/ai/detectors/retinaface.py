"""
RetinaFace - высокоточный детектор
"""

import sys
from pathlib import Path

from .base import BaseDetector, DetectedFace, ModuleStatus


class RetinaFace(BaseDetector):
    """
    RetinaFace - высокоточный детектор с атрибутами
    
    Пока не реализован.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info.version = "0.1"
        self.info.provider = "GPU"
        self.info.description = "RetinaFace детектор (Multi-scale)"
        self.info.status = ModuleStatus.NOT_INSTALLED

    async def load_models(self) -> bool:
        """Загрузить модели детектора"""
        return await self.initialize()

    async def unload_models(self) -> bool:
        """Выгрузить модели детектора"""
        return await super().unload_models()

    async def detect(self, image_bytes: bytes, det_size: int = 640) -> list:
        """Детектировать лица на изображении"""
        raise NotImplementedError(f"{self.info.name} is not yet implemented. Falling back to SCRFD.")

    async def detect_with_embedding(self, image_bytes: bytes, det_size: int = 640) -> list:
        """Детектировать лица и извлечь эмбеддинги"""
        raise NotImplementedError(f"{self.info.name} is not yet implemented. Falling back to SCRFD.")
