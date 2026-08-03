"""
Detectors package

Модули детекции лиц:
- SCRFD (InsightFace) - текущий детектор
- YOLO-Face - детектор на основе YOLO
- RetinaFace - высокоточный детектор
"""

from .scrfd import SCRFD
from .yoloface import YOLOFace
from .retinaface import RetinaFace

__all__ = ['SCRFD', 'YOLOFace', 'RetinaFace']
