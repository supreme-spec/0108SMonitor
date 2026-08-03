"""
SCRFD - детектор InsightFace
"""

from .base import BaseDetector, DetectedFace


class SCRFD(BaseDetector):
    """
    SCRFD (Speed and Accuracy) - детектор из InsightFace
    
    Используется как основной детектор в системе.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info.version = "1.0"
        self.info.provider = "CUDA"
        self.info.description = "SCRFD детектор от InsightFace (buffalo_l)"

    async def detect(self, image_bytes: bytes) -> list:
        """Детектировать лица на изображении"""
        # TODO: Реализовать детекцию через Python-сервер
        return []

    async def detect_with_embedding(self, image_bytes: bytes) -> list:
        """Детектировать лица и извлечь эмбеддинги"""
        # TODO: Реализовать детекцию с эмбеддингами
        return []
