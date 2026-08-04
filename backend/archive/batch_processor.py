"""
Batch Archive Processor with Database Integration

Модуль для массовой обработки архива с записью в БД:
- Папка → Episode → ArchivePhoto → ArchiveFace
- Кластеризация → EpisodePerson → Person (связывание)
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

import numpy as np

# Добавляем пути к библиотекам
AI_LIBS_DIR = Path(r"D:\AI_Libraries")
sys.path.insert(0, str(AI_LIBS_DIR / "insightface-master" / "insightface-master" / "python-package"))

from insightface.utils import face_align

from .config import MODELS_DIR, PROFILES, FACE_API_KEY
from .quality import calculate_composite_quality
from .cluster import GreedyClusterer
from .profile_classifier import classify_source_profile
from .ocr import extract_osd_text, extract_timestamp, extract_camera_id
from .processor import ArchiveProcessor


class BatchArchiveProcessor:
    """
    Batch processor с интеграцией в БД
    """
    
    def __init__(self, prisma_client=None):
        """
        Args:
            prisma_client: Prisma Client для доступа к БД
        """
        self.prisma = prisma_client
        self.processor = ArchiveProcessor()
    
    def process_folder(self, folder_path: str, episode_name: str = None) -> Dict:
        """
        Обработать папку и записать в БД
        
        Args:
            folder_path: путь к папке с фото
            episode_name: имя эпизода (если None, используется имя папки)
        
        Returns:
            dict с результатами
        """
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}
        
        # Определение имени эпизода
        if episode_name is None:
            episode_name = folder.name
        
        # Авто-определение профиля
        profile = classify_source_profile(folder)
        
        # Создание или получение Episode
        episode = self._create_or_get_episode(folder, episode_name, profile)
        
        if not episode:
            return {"error": "Failed to create episode"}
        
        # Обработка фото
        image_files = sorted([
            f for f in folder.iterdir()
            if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
        ])
        
        results = {
            "episode_id": episode.id,
            "episode_name": episode_name,
            "folder": str(folder),
            "profile": profile,
            "photos_count": len(image_files),
            "photos_processed": 0,
            "faces_detected": 0,
            "persons_found": 0,
            "persons_unknown": 0,
            "error": None,
            "photos": [],
        }
        
        try:
            for img_path in image_files:
                photo_result = self._process_single_photo(img_path, episode, profile)
                results["photos"].append(photo_result)
                results["photos_processed"] += 1
                results["faces_detected"] += len(photo_result.get("faces", []))
            
            # Кластеризация и связывание с персонами
            cluster_result = self._cluster_and_link(episode, results["photos"])
            results["persons_found"] = cluster_result.get("persons_found", 0)
            results["persons_unknown"] = cluster_result.get("persons_unknown", 0)
            
            # Синхронизация FAISS индекса
            sync_result = self._sync_faiss_index()
            results["faiss_sync"] = sync_result
            
            # Обновление статуса эпизода
            self.prisma.episode.update(
                where={"id": episode.id},
                data={
                    "status": "completed",
                    "processed_at": datetime.now(),
                }
            )
            
        except Exception as e:
            results["error"] = str(e)
            self.prisma.episode.update(
                where={"id": episode.id},
                data={
                    "status": "failed",
                    "error_message": str(e),
                }
            )
        
        return results
    
    def _create_or_get_episode(self, folder: Path, episode_name: str, profile: str):
        """Создать или получить существующий Episode"""
        folder_path = str(folder)
        
        episode = self.prisma.episode.find_unique(
            where={"folder_path": folder_path}
        )
        
        if not episode:
            # Авто-извлечение метаданных из OSD
            osd_text = None
            first_img = next(folder.iterdir(), None)
            if first_img:
                try:
                    import cv2
                    from PIL import Image, ImageOps
                    pil_img = Image.open(first_img)
                    if pil_img.mode in ('CMYK', 'P', 'RGBA', 'LA'):
                        pil_img = pil_img.convert('RGB')
                    pil_img = ImageOps.exif_transpose(pil_img)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    osd_text = extract_osd_text(img)
                except Exception:
                    pass
            
            # Декодирование OSD
            camera_id = extract_camera_id(osd_text) if osd_text else None
            capture_time = extract_timestamp(osd_text) if osd_text else None
            
            episode = self.prisma.episode.create(
                data={
                    "folder_path": folder_path,
                    "episode_name": episode_name,
                    "source_type": profile.replace("_", "-"),
                    "osd_text": osd_text,
                    "capture_time": capture_time,
                    "camera_name": camera_id,
                    "status": "processing",
                }
            )
        
        return episode
    
    def _process_single_photo(self, img_path: Path, episode, profile: str):
        """Обработать одно фото и записать в БД"""
        try:
            import cv2
            from PIL import Image, ImageOps
            
            # Загрузка с конвертацией CMYK/P/RGBA в RGB
            pil_img = Image.open(img_path)
            if pil_img.mode in ('CMYK', 'P', 'RGBA', 'LA'):
                pil_img = pil_img.convert('RGB')
            pil_img = ImageOps.exif_transpose(pil_img)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Детекция
            faces = self.processor.app.get(img)
            
            # Извлечение OSD
            osd_text = extract_osd_text(img)
            
            # Создание ArchivePhoto
            photo = self.prisma.archive_photo.create(
                data={
                    "episode_id": episode.id,
                    "photo_path": str(img_path),
                    "filename": img_path.name,
                    "width": img.shape[1],
                    "height": img.shape[0],
                    "source_type": "camera_photo",
                    "osd_text": osd_text,
                    "profile": profile,
                    "status": "processing",
                }
            )
            
            # Обработка лиц
            face_results = []
            for i, face in enumerate(faces):
                x1, y1, x2, y2 = face.bbox.astype(int)
                w, h = x2 - x1, y2 - y1
                
                # Качество
                crop = img[y1:y2, x1:y2]
                quality = calculate_composite_quality(
                    crop, face.bbox, face.kps, (img.shape[1], img.shape[0])
                )
                
                # Эмбеддинг
                embedding = face.normed_embedding.tolist()
                
                # Создание ArchiveFace
                archive_face = self.prisma.archive_face.create(
                    data={
                        "photo_id": photo.id,
                        "bbox_x": float(x1),
                        "bbox_y": float(y1),
                        "bbox_w": float(w),
                        "bbox_h": float(h),
                        "det_score": float(face.det_score),
                        "kps": json.dumps(face.kps.tolist()) if face.kps is not None else None,
                        "pitch_deg": quality.get("pitch", 0.0),
                        "yaw_deg": quality.get("yaw", 0.0),
                        "blur_score": quality.get("blur_score", 0.0),
                        "brightness": quality.get("brightness", 0.0),
                        "occlusion": quality.get("occlusion_score", 0.0),
                        "quality_score": quality.get("quality_score", 0.0),
                        "tier": quality.get("tier", "D"),
                        "embedding": json.dumps(embedding),
                        "embedding_model": "buffalo_l",
                        "status": "detected",
                    }
                )
                
                face_results.append({
                    "face_id": archive_face.id,
                    "bbox": [float(x1), float(y1), float(w), float(h)],
                    "quality": quality,
                    "tier": quality.get("tier", "D"),
                })
            
            # Обновление статуса фото
            self.prisma.archive_photo.update(
                where={"id": photo.id},
                data={
                    "status": "completed",
                    "processed_at": datetime.now(),
                }
            )
            
            return {
                "photo_id": photo.id,
                "faces": face_results,
            }
            
        except Exception as e:
            return {
                "photo_id": None,
                "error": str(e),
            }
    
    def _cluster_and_link(self, episode, photos: List[Dict]):
        """
        Кластеризация и связывание с персонами
        
        Алгоритм:
        1. Собрать все эмбеддинги из фото
        2. Кластеризация по косинусу (T_INTRA)
        3. Попытка связать с существующими персонами
        4. Создать EpisodePerson для каждого кластера
        """
        # Сбор эмбеддингов
        all_faces = []
        for photo in photos:
            for face in photo.get("faces", []):
                if face.get("quality", {}).get("quality_score", 0) >= 0.3:
                    all_faces.append(face)
        
        if len(all_faces) == 0:
            return {"persons_found": 0, "persons_unknown": 0}
        
        # Извлечение эмбеддингов
        embeddings = []
        for face in all_faces:
            if face.get("quality", {}).get("embedding"):
                emb = np.array(json.loads(face["quality"]["embedding"]))
                embeddings.append(emb)
        
        if len(embeddings) == 0:
            return {"persons_found": 0, "persons_unknown": 0}
        
        # Кластеризация
        clusterer = GreedyClusterer(threshold=0.55)
        clusters = clusterer.cluster(np.array(embeddings))
        
        # Связывание с персонами
        persons_found = 0
        persons_unknown = 0
        
        for cluster_id, member_indices in clusters.items():
            # Получить best face в кластере (по качеству)
            best_face = max([all_faces[i] for i in member_indices], 
                          key=lambda f: f.get("quality", {}).get("quality_score", 0))
            
            # Попытка найти в БД
            person = self._find_person_by_embedding(
                np.array(json.loads(best_face["quality"]["embedding"]))
            )
            
            if person:
                # Существующая персона
                persons_found += 1
                
                # Создание EpisodePerson
                episode_person = self.prisma.episode_person.create(
                    data={
                        "episode_id": episode.id,
                        "person_id": person.id,
                        "person_name": person.name,
                        "role": self._determine_role(person, episode),  # target/ignore/svita
                        "confidence": 0.9,
                        "label_source": "auto",
                        "cluster_id": f"C{cluster_id:03d}",
                    }
                )
                
                # Обновление лиц
                for idx in member_indices:
                    self.prisma.archive_face.update(
                        where={"id": all_faces[idx]["face_id"]},
                        data={
                            "episode_person_id": episode_person.id,
                            "status": "embedding_extracted",
                        }
                    )
            else:
                # Новая персона (unknown)
                persons_unknown += 1
                
                # Создание EpisodePerson без person_id
                episode_person = self.prisma.episode_person.create(
                    data={
                        "episode_id": episode.id,
                        "person_name": f"Unknown_{cluster_id:03d}",
                        "role": "unknown",
                        "confidence": 0.5,
                        "label_source": "auto",
                        "cluster_id": f"C{cluster_id:03d}",
                    }
                )
                
                # Обновление лиц
                for idx in member_indices:
                    self.prisma.archive_face.update(
                        where={"id": all_faces[idx]["face_id"]},
                        data={
                            "episode_person_id": episode_person.id,
                        }
                    )
        
        return {"persons_found": persons_found, "persons_unknown": persons_unknown}
    
    def _sync_faiss_index(self) -> Dict:
        """
        Синхронизировать FAISS индекс после записи новых эмбеддингов
        Вызывает /update-index с актуальными персонами
        """
        if not self.prisma:
            return {"status": "skipped", "reason": "No prisma client"}
        
        if not FACE_API_KEY:
            return {"status": "skipped", "reason": "FACE_API_KEY not configured"}
        
        try:
            # Получить всех персон с эмбеддингами
            persons = self.prisma.person.find_many(
                where={"embedding_count": {"gt": 0}},
                include={"descriptors": True}
            )
            
            persons_list = []
            for person in persons:
                for desc in person.descriptors:
                    try:
                        emb = json.loads(desc.descriptor)
                        persons_list.append({
                            "id": person.id,
                            "name": person.name,
                            "embedding": emb,
                        })
                    except Exception:
                        continue
            
            # Вызвать /update-index
            response = requests.post(
                "http://localhost:8001/update-index",
                json={"persons": persons_list},
                headers={"X-API-Key": FACE_API_KEY},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "ok",
                    "indexed": result.get("indexed", 0),
                    "vectors": result.get("total_vectors", 0),
                }
            else:
                return {
                    "status": "error",
                    "code": response.status_code,
                    "message": response.text,
                }
                
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def _find_person_by_embedding(self, embedding: np.ndarray, threshold: float = 0.55):
        """Найти персону по эмбеддингу"""
        # Получить всех людей с эмбеддингами
        persons = self.prisma.person.find_many(
            where={"embedding_count": {"gt": 0}},
            include={"descriptors": True}
        )
        
        for person in persons:
            for desc in person.descriptors:
                try:
                    db_emb = np.array(json.loads(desc.descriptor))
                    sim = float(np.dot(embedding, db_emb))
                    if sim >= threshold:
                        return person
                except Exception:
                    continue
        
        return None
    
    def _determine_role(self, person, episode):
        """Определить роль персоны в эпизоде"""
        # По умолчанию - target (искомое)
        # Можно добавить логику на основе:
        # - Должности персоны
        # - Зоны камеры
        # - Времени суток
        
        return "target"


# Пример использования
if __name__ == "__main__":
    # Для теста без Prisma
    processor = BatchArchiveProcessor(prisma_client=None)
    result = processor.process_folder(
        r"D:\bd_gosti\test_dataset\ceiling",
        "Test Episode"
    )
    print(json.dumps(result, indent=2, default=str))
