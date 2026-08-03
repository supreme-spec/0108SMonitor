"""
Базовый класс для детекторов
"""

import sys
from pathlib import Path
from abc import abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from PIL import Image
import io

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo
from ..common.insightface_loader import load_insightface


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
        self._face_app: Optional[Any] = None
        self._models_dir: Path = Path(__file__).parent.parent.parent.parent / "models"

    async def initialize(self) -> bool:
        """Инициализировать детектор"""
        try:
            self._face_app = load_insightface(str(self._models_dir))
            self.info.enabled = True
            self.info.status = ModuleStatus.LOADED
            return True
        except Exception as e:
            print(f"Failed to initialize {self.__class__.__name__}: {e}")
            self.info.status = ModuleStatus.ERROR
            return False

    async def unload_models(self) -> bool:
        """Выгрузить модели"""
        self._face_app = None
        self.info.enabled = False
        self.info.status = ModuleStatus.UNLOADED
        return True

    @abstractmethod
    async def detect(self, image_bytes: bytes) -> List[DetectedFace]:
        """Детектировать лица на изображении"""
        pass

    @abstractmethod
    async def detect_with_embedding(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Детектировать лица и извлечь эмбеддинги"""
        pass
