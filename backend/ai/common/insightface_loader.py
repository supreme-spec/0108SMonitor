"""
Common InsightFace loader - singleton pattern
"""

import sys
from pathlib import Path
from typing import Optional

import onnxruntime as ort


class InsightFaceLoader:
    """Singleton loader for InsightFace FaceAnalysis"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._face_app = None
        self._models_dir = Path(__file__).parent.parent.parent.parent / "models"
        self._initialized = True
    
    def load(self, models_dir: str = None) -> Optional[Any]:
        """Load InsightFace FaceAnalysis instance"""
        if self._face_app is not None:
            return self._face_app
        
        from insightface.app import FaceAnalysis
        
        target_providers = self._get_optimal_providers()
        
        if models_dir:
            self._models_dir = Path(models_dir)
        
        try:
            self._face_app = FaceAnalysis(
                name="buffalo_l", 
                root=str(self._models_dir), 
                providers=target_providers
            )
            self._face_app.prepare(ctx_id=0 if "CUDA" in target_providers else -1, det_size=(640, 640))
            return self._face_app
        except Exception as e:
            print(f"Failed to load InsightFace: {e}")
            self._face_app = None
            return None
    
    def get(self) -> Optional[Any]:
        """Get loaded FaceAnalysis instance"""
        return self._face_app
    
    def _get_optimal_providers(self) -> list:
        """Get optimal execution providers"""
        available = ort.get_available_providers()
        providers = []
        
        if "CUDAExecutionProvider" in available:
            providers.append("CUDAExecutionProvider")
        elif "DmlExecutionProvider" in available:
            providers.append("DmlExecutionProvider")
        elif "OpenVINOExecutionProvider" in available:
            providers.append("OpenVINOExecutionProvider")
        
        providers.append("CPUExecutionProvider")
        return providers


def load_insightface(models_dir: str = None) -> Optional[Any]:
    """Convenience function to get InsightFace instance"""
    loader = InsightFaceLoader()
    return loader.load(models_dir)


def get_insightface() -> Optional[Any]:
    """Convenience function to get already loaded instance"""
    loader = InsightFaceLoader()
    return loader.get()