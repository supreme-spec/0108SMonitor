"""
YOLO-Face - детектор на основе YOLO
"""

import sys
from pathlib import Path

from .base import BaseDetector, DetectedFace, ModuleStatus


class YOLOFace(BaseDetector):
    """
    YOLO-Face - детектор на основе YOLOv8
    
    Пока не реализован.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info.version = "0.1"
        self.info.provider = "GPU"
        self.info.description = "YOLO-Face детектор (YOLOv8)"
        self.info.status = ModuleStatus.NOT_INSTALLED

    async def load_models(self) -> bool:
        """Загрузить модели детектора"""
        return await self.initialize()

    async def unload_models(self) -> bool:
        """Выгрузить модели детектора"""
        return await super().unload_models()

    async def detect(self, image_bytes: bytes) -> list:
        """Детектировать лица на изображении"""
        # TODO: Реализовать детекцию через Python-сервер
        return []

    async def detect_with_embedding(self, image_bytes: bytes) -> list:
        """Детектировать лица и извлечь эмбеддинги"""
        # TODO: Реализовать детекцию с эмбеддингами
        return []
