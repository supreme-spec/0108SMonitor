"""
Batch Archive Processor

Основной модуль для обработки папок с фото:
- Авто-определение профиля источника
- Детекция лиц с SCRFD
- Извлечение эмбеддингов (ArcFace/AdaFace)
- Кластеризация по людям внутри эпизода
- Связывание с персонами из БД
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from PIL import Image, ImageOps

# Добавляем пути к библиотекам
AI_LIBS_DIR = Path(r"D:\AI_Libraries")
sys.path.insert(0, str(AI_LIBS_DIR / "insightface-master" / "insightface-master" / "python-package"))
sys.path.insert(0, str(AI_LIBS_DIR / "AdaFace-master" / "AdaFace-master"))
sys.path.insert(0, str(AI_LIBS_DIR / "ArcFace-main" / "ArcFace-main"))

import cv2
from insightface.app import FaceAnalysis
from insightface.utils import face_align

from .config import MODELS_DIR, PROFILES, get_model_paths
from .quality import calculate_composite_quality
from .cluster import UnionFindClusterer as Clusterer, deduplicate_faces, merge_clusters_by_similarity
from .profile_classifier import classify_source_profile
from .ocr import extract_osd_text


class ArchiveProcessor:
    """
    Основной процессор для batch-обработки архива
    """
    
    def __init__(self, profile: str = "auto", detector_name: str = "scrfd"):
        """
        Args:
            profile: имя профиля обработки ('auto' для авто-определения)
            detector_name: 'scrfd' или 'retinaface'
        """
        self.profile = profile
        self.detector_name = detector_name
        
        # Инициализация FaceAnalysis
        self.app = self._init_face_analysis()
    
    def _init_face_analysis(self) -> FaceAnalysis:
        """Инициализация FaceAnalysis с адаптивным det_size"""
        # Используем CPU (ctx_id=-1) по умолчанию для стабильности
        # Если нужен GPU, передайте ctx_id=0 через config или окружение
        providers = ['CPUExecutionProvider']
        ctx_id = -1
        
        app = FaceAnalysis(
            name='buffalo_l',
            root=str(MODELS_DIR),
            providers=providers
        )
        
        # Адаптивный det_size: 1024 -> 640 -> 1600
        for det_size_val in [1024, 640, 1600]:
            try:
                app.prepare(ctx_id=ctx_id, det_size=(det_size_val, det_size_val))
                # Пробный тест - использовать минимальное изображение
                test_img = np.zeros((640, 480, 3), dtype=np.uint8)
                faces = app.get(test_img)
                print(f"Detected {len(faces)} faces with det_size={det_size_val}, ctx_id={ctx_id} (CPU mode)")
                break
            except Exception as e:
                print(f"det_size={det_size_val}, ctx_id={ctx_id} failed: {e}")
                if det_size_val == 1600:
                    raise RuntimeError(f"Failed to initialize FaceAnalysis: {e}")
        
        return app
    
    def process_folder(self, folder_path: str, episode_name: str = None) -> Dict:
        """
        Обработать папку с фото
        
        Args:
            folder_path: путь к папке с фото
            episode_name: имя эпизода (если None, используется имя папки)
        
        Returns:
            dict с результатами обработки
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Определение имени эпизода
        if episode_name is None:
            episode_name = folder.name
        
        # Авто-определение профиля
        if self.profile == "auto":
            self.profile = classify_source_profile(folder)
        
        print(f"Processing {folder.name} with profile: {self.profile}")
        
        # Получение фото
        image_files = sorted([
            f for f in folder.iterdir()
            if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
        ])
        
        if not image_files:
            return {"error": "No image files found", "photos_count": 0}
        
        results = {
            "folder": str(folder),
            "episode_name": episode_name,
            "profile": self.profile,
            "photos": [],
            "faces": [],
            "clusters": {},
            "persons_found": 0,
            "persons_unknown": 0,
            "error": None,
        }
        
        # Обработка каждого фото
        for img_path in image_files:
            photo_result = self._process_image(img_path)
            results["photos"].append(photo_result)
            results["faces"].extend(photo_result["faces"])
        
        # Кластеризация лиц
        if len(results["faces"]) > 0:
            results["clusters"] = self._cluster_faces(results["faces"])
            results["persons_found"] = len([
                f for f in results["faces"] 
                if f.get("cluster_id") is not None
            ])
        
        return results
    
    def _process_image(self, img_path: Path) -> Dict:
        """Обработать одно изображение"""
        # Загрузка с конвертацией CMYK/P/RGBA в RGB
        pil_img = Image.open(img_path)
        if pil_img.mode in ('CMYK', 'P', 'RGBA', 'LA'):
            pil_img = pil_img.convert('RGB')
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Получение размеров
        height, width = img.shape[:2]
        
        # Детекция лиц
        faces = self.app.get(img)
        
        photo_result = {
            "path": str(img_path),
            "filename": img_path.name,
            "width": width,
            "height": height,
            "faces": [],
            "osd_text": None,
        }
        
        # Извлечение OSD текста
        photo_result["osd_text"] = extract_osd_text(img)
        
        # Обработка каждого лица
        for i, face in enumerate(faces):
            face_result = self._process_face(face, img, i)
            photo_result["faces"].append(face_result)
        
        return photo_result
    
    def _process_face(self, face, img: np.ndarray, face_idx: int) -> Dict:
        """Обработать одно лицо"""
        # Координаты bbox
        x1, y1, x2, y2 = face.bbox.astype(int)
        w, h = x2 - x1, y2 - y1
        
        # Вырезаем лицо и делаем contiguous (для совместимости с OpenCV)
        face_image = img[y1:y2, x1:x2].copy()
        
        # Качество
        quality_result = calculate_composite_quality(
            face_image,
            np.array([x1, y1, w, h]),
            face.kps,
            (img.shape[1], img.shape[0])
        )
        
        # Эмбеддинг
        embedding = face.normed_embedding
        
        return {
            "face_idx": face_idx,
            "bbox": [float(x1), float(y1), float(w), float(h)],
            "det_score": float(face.det_score),
            "kps": face.kps.tolist() if face.kps is not None else None,
            "pitch_deg": quality_result.get("pitch", 0.0),
            "yaw_deg": quality_result.get("yaw", 0.0),
            "blur_score": quality_result.get("blur_score", 0.0),
            "brightness": quality_result.get("brightness", 0.0),
            "occlusion": quality_result.get("occlusion_score", 0.0),
            "quality_score": quality_result.get("quality_score", 0.0),
            "tier": quality_result.get("tier", "D"),
            "embedding": embedding.tolist(),
            "cluster_id": None,  # будет установлено после кластеризации
        }
    
    def _cluster_faces(self, faces: List[Dict]) -> Dict:
        """Кластеризация лиц по идентичности"""
        if len(faces) == 0:
            return {}
        
        # Извлечение эмбеддингов
        embeddings = np.array([f["embedding"] for f in faces])
        
        # Кластеризация
        clusterer = Clusterer(threshold=0.45)
        clusters = clusterer.cluster(embeddings)
        
        # Назначение cluster_id
        face_to_cluster = {}
        for cluster_id, members in clusters.items():
            for idx in members:
                faces[idx]["cluster_id"] = f"C{cluster_id:03d}"
                face_to_cluster[faces[idx]["face_idx"]] = f"C{cluster_id:03d}"
        
        return {
            "clusters": {
                cid: [faces[idx]["face_idx"] for idx in members]
                for cid, members in clusters.items()
            },
            "face_to_cluster": face_to_cluster,
        }
    
    def get_faces_by_profile(self, folder_path: str) -> List[Dict]:
        """Получить все лица с кропами для профиля"""
        result = self.process_folder(folder_path)
        
        # Генерация кропов
        for photo in result.get("photos", []):
            img_path = Path(photo["path"])
            img = cv2.imread(str(img_path))
            
            for face in photo.get("faces", []):
                x1, y1, w, h = map(int, face["bbox"])
                crop = img[y1:y1+h, x1:x1+w]
                face["crop_path"] = None  # будет сохранено
    
        return result


# Пример использования
if __name__ == "__main__":
    processor = ArchiveProcessor()
    result = processor.process_folder(r"D:\bd_gosti\test_dataset\ceiling")
    print(json.dumps(result, indent=2, default=str))
