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
        """Internal detection using InsightFace with letterbox resize"""
        if not self._face_app:
            self._face_app = get_insightface()
            if not self._face_app:
                self._face_app = load_insightface(str(self._models_dir))
                if not self._face_app:
                    return []

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = np.array(img.convert("RGB"))
            orig_h, orig_w = img_rgb.shape[:2]
            target = int(det_size)

            if orig_w != target or orig_h != target:
                scale = min(target / orig_w, target / orig_h)
                new_w = int(round(orig_w * scale))
                new_h = int(round(orig_h * scale))
                img_resized = np.array(Image.fromarray(img_rgb).resize((new_w, new_h), Image.Resampling.LANCZOS))
                canvas = np.zeros((target, target, 3), dtype=img_resized.dtype)
                pad_x = (target - new_w) // 2
                pad_y = (target - new_h) // 2
                canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = img_resized
                img_rgb = canvas
            else:
                scale = 1.0
                pad_x = 0
                pad_y = 0

            det_thresh = self.config.get('min_det_score', 0.5) if self.config else 0.5
            faces = self._face_app.get(img_rgb, det_thresh=det_thresh, max_num=20)

            results = []
            for face in faces:
                bbox = face.bbox.astype(float).tolist()
                x1, y1, x2, y2 = bbox[:4]
                x1 = (x1 - pad_x) / scale
                y1 = (y1 - pad_y) / scale
                x2 = (x2 - pad_x) / scale
                y2 = (y2 - pad_y) / scale
                result = {
                    "bbox": [x1, y1, x2, y2],
                    "det_score": float(face.det_score),
                    "kps": [],
                    "age": int(face.age) if hasattr(face, "age") else None,
                    "gender": int(face.gender) if hasattr(face, "gender") else None,
                }
                if hasattr(face, "kps") and face.kps is not None:
                    kps = face.kps.astype(float).tolist()
                    result["kps"] = [[(pt[0] - pad_x) / scale, (pt[1] - pad_y) / scale] for pt in kps]

                if with_embedding and hasattr(face, "embedding") and face.embedding is not None:
                    result["embedding"] = face.embedding.astype(float).tolist()

                results.append(result)

            return results

        except Exception as e:
            print(f"SCRFD detection error: {e}")
            return []
