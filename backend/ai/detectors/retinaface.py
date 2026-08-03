"""
RetinaFace - высокоточный детектор
"""

from .base import BaseDetector, DetectedFace


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

    async def detect(self, image_bytes: bytes) -> list:
        """Детектировать лица на изображении"""
        # TODO: Реализовать детекцию через Python-сервер
        return []

    async def detect_with_embedding(self, image_bytes: bytes) -> list:
        """Детектировать лица и извлечь эмбеддинги"""
        # TODO: Реализовать детекцию с эмбеддингами
        return []
