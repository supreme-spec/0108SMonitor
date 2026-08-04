"""
SCRFD - детектор InsightFace
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image
import io

from .base import BaseDetector, DetectedFace
from ..common.insightface_loader import load_insightface, get_insightface


class SCRFD(BaseDetector):
    """
    SCRFD (Speed and Accuracy) - детектор из InsightFace
    
    Используется как основной детектор в системе.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info.version = "10GF"
        self.info.provider = "CUDA"
        self.info.description = "SCRFD детектор от InsightFace (buffalo_l)"

    async def load_models(self) -> bool:
        """Загрузить модели детектора"""
        return await self.initialize()

    async def unload_models(self) -> bool:
        """Выгрузить модели детектора"""
        return await super().unload_models()

    async def detect(self, image_bytes: bytes, det_size: int = 640) -> List[DetectedFace]:
        """Детектировать лица на изображении"""
        faces = await self._detect_internal(image_bytes, with_embedding=False, det_size=det_size)
        return [
            DetectedFace(
                box=f.get("bbox", [0, 0, 0, 0]),
                score=f.get("det_score", 0),
                landmarks=f.get("kps"),
                embedding=None,
            )
            for f in faces
        ]

    async def detect_with_embedding(self, image_bytes: bytes, det_size: int = 640) -> List[Dict[str, Any]]:
        """Детектировать лица и извлечь эмбеддинги"""
        return await self._detect_internal(image_bytes, with_embedding=True, det_size=det_size)

    async def _detect_internal(self, image_bytes: bytes, with_embedding: bool = True, det_size: int = 640) -> List[Any]:
        """Internal detection using InsightFace"""
        if not self._face_app:
            # Try to load if not initialized
            self._face_app = get_insightface()
            if not self._face_app:
                self._face_app = load_insightface(str(self._models_dir))
                if not self._face_app:
                    return []
        
        try:
            # Decode image
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = np.array(img.convert("RGB"))
            
            # Resize to target det_size if needed
            target = (det_size, det_size)
            if img_rgb.shape[:2] != target:
                img_rgb = np.array(Image.fromarray(img_rgb).resize(target, Image.Resampling.LANCZOS))
            
            # Detect faces
            faces = self._face_app.get(img_rgb)
            
            results = []
            for face in faces:
                result = {
                    "bbox": face.bbox.astype(float).tolist(),
                    "det_score": float(face.det_score),
                    "kps": face.kps.astype(float).tolist() if hasattr(face, "kps") else None,
                    "age": int(face.age) if hasattr(face, "age") else None,
                    "gender": int(face.gender) if hasattr(face, "gender") else None,
                }
                
                if with_embedding and hasattr(face, "embedding") and face.embedding is not None:
                    result["embedding"] = face.embedding.astype(float).tolist()
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"SCRFD detection error: {e}")
            return []
