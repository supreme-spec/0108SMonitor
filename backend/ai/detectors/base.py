"""
Базовый класс для детекторов
"""

from abc import abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo


@dataclass
class DetectedFace:
    """Результат детекции одного лица"""
    box: List[float]  # [x, y, w, h]
    score: float
    landmarks: List[float] = None
    embedding: List[float] = None


class BaseDetector(BaseModule):
    """Базовый класс для детекторов лиц"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.info = ModuleInfo(
            name=self.__class__.__name__,
            type=ModuleType.DETECTOR,
            version=None,
            provider="CPU",
            enabled=False,
            status=ModuleStatus.NOT_INSTALLED
        )

    @abstractmethod
    async def detect(self, image_bytes: bytes) -> List[DetectedFace]:
        """Детектировать лица на изображении"""
        pass

    @abstractmethod
    async def detect_with_embedding(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Детектировать лица и извлечь эмбеддинги"""
        pass
