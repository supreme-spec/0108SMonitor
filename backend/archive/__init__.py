"""
Batch Archive Processor Module

Интегрированные библиотеки из D:\AI_Libraries:
- insightface-master (SCRFD + ArcFace/AdaFace)
- AdaFace-master (quality-adaptive эмбеддинги)
- ArcFace-main (классический ArcFace)
- retinaface-master (альтернативный детектор)
- yolo-face-dev (быстрый префильтр)
- faiss-main (векторный индекс)
- onnxruntime (GPU и CPU инференс)
"""

__version__ = "1.0.0"
__all__ = [
    "config", "processor", "quality", "cluster", "profiles",
    "intake", "ocr", "profile_classifier", "batch_processor"
]

# Импорт основных модулей
from . import config
from .processor import ArchiveProcessor
from .quality import calculate_composite_quality
from .cluster import GreedyClusterer
from .intake import PersonIntakePipeline
from .profile_classifier import classify_source_profile
from .ocr import extract_osd_text
from .batch_processor import BatchArchiveProcessor
