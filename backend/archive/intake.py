"""
Intake Pipeline for Person Enrollment

Обработка папок персонала (до 20 фото на человека):
- Quality-гейт ( tier A required для зачисления)
- Дедупликация по косинусу
- Diversity-отбор (разные ракурсы/свет)
- Проверка "свой/чужой" внутри набора и против БД
- Генерация ч/б-близнецов
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib

import numpy as np
from PIL import Image, ImageOps

# Добавляем пути к библиотекам
AI_LIBS_DIR = Path(r"D:\AI_Libraries")
sys.path.insert(0, str(AI_LIBS_DIR / "insightface-master" / "insightface-master" / "python-package"))

import cv2
from insightface.app import FaceAnalysis
from insightface.utils import face_align

from .config import MODELS_DIR, DEFAULT_CONFIG
from .quality import calculate_composite_quality
from .cluster import deduplicate_faces, GreedyClusterer
from .processor import ArchiveProcessor


class PersonIntakePipeline:
    """
    Пайплайн зачисления персонала
    """
    
    def __init__(self, prisma_client=None):
        """
        Args:
            prisma_client: Prisma Client для доступа к БД (опционально)
        """
        self.prisma = prisma_client
        self.app = self._init_face_analysis()
    
    def _init_face_analysis(self) -> FaceAnalysis:
        """Инициализация FaceAnalysis с адаптивным det_size"""
        app = FaceAnalysis(
            name='buffalo_l',
            root=str(MODELS_DIR),
            providers=['CPUExecutionProvider']
        )
        
        # Адаптивный det_size для разных размеров изображений
        # Попробуем с меньшего (640) к большему (1280) для больших изображений
        for det_size_val in [640, 1024, 1280]:
            try:
                app.prepare(ctx_id=-1, det_size=(det_size_val, det_size_val))
                print(f"PersonIntake: FaceAnalysis prepared with det_size={det_size_val}, ctx_id=-1 (CPU mode)")
                break
            except Exception as e:
                print(f"PersonIntake: det_size={det_size_val} failed: {e}")
                if det_size_val == 1280:
                    raise RuntimeError(f"Failed to initialize FaceAnalysis for PersonIntakePipeline: {e}")
        
        return app
    
    def process_folder(self, folder_path: str, person_name: str) -> Dict:
        """
        Обработать папку с фото персонала
        
        Args:
            folder_path: путь к папке с фото
            person_name: имя персоны
        
        Returns:
            dict с результатами и отчётом
        """
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}
        
        # Получение фото
        image_files = sorted([
            f for f in folder.iterdir()
            if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
        ])
        
        if not image_files:
            return {"error": "No image files found", "photos_count": 0}
        
        report = {
            "folder": str(folder),
            "person_name": person_name,
            "photos_count": len(image_files),
            "photos_processed": 0,
            "photos_passed_quality": 0,
            "photos_duplicate": 0,
            "photos_diversity_selected": 0,
            "photos_too_small": 0,
            "photos_blurred": 0,
            "photos_rejected": 0,
            "embeddings_generated": 0,
            "bw_twin_generated": 0,
            "report": [],
        }
        
        # Список для дедупликации
        all_embeddings = []  # (emb_color, emb_bw, path, metrics)
        
        # Обработка каждого фото
        for img_path in image_files:
            result = self._process_single_image(img_path, person_name)
            
            if result["status"] == "passed":
                all_embeddings.append(result)
                report["photos_processed"] += 1
                report["photos_passed_quality"] += 1
            else:
                report["photos_rejected"] += 1
                if result["status"] == "too_small":
                    report["photos_too_small"] += 1
                elif result["status"] == "blurred":
                    report["photos_blurred"] += 1
                elif result["status"] == "duplicate":
                    report["photos_duplicate"] += 1
            
            report["report"].append(result)
        
        # Дедупликация
        unique_embeddings, duplicate_map = self._deduplicate(all_embeddings)
        report["photos_duplicate"] += len(all_embeddings) - len(unique_embeddings)
        
        # Diversity-отбор (максимум 8 цветных фото)
        selected = self._select_diverse(unique_embeddings, max_count=8)
        report["photos_diversity_selected"] = len(selected)
        
        # Генерация ч/б-близнецов
        final_templates = []
        for emb in selected:
            final_templates.append({
                "type": "color",
                "embedding": emb["emb_color"],
                "path": emb["path"],
                "metrics": emb["metrics"],
            })
            final_templates.append({
                "type": "bw_twin",
                "embedding": emb["emb_bw"],
                "path": emb["path"],
                "metrics": emb["metrics"],
            })
            report["bw_twin_generated"] += 1
        
        report["embeddings_generated"] = len(final_templates)
        
        # Статус завершения
        report["status"] = "completed" if len(final_templates) >= 2 else "failed"
        
        return report
    
    def _process_single_image(self, img_path: Path, person_name: str) -> Dict:
        """Обработать одно фото"""
        try:
            # Загрузка с конвертацией CMYK/P/RGBA в RGB
            pil_img = Image.open(img_path)
            if pil_img.mode in ('CMYK', 'P', 'RGBA', 'LA'):
                pil_img = pil_img.convert('RGB')
            pil_img = ImageOps.exif_transpose(pil_img)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            full_bw = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
            
            # Детекция
            faces = self.app.get(img)
            
            if len(faces) == 0:
                return {
                    "path": str(img_path),
                    "status": "no_face",
                    "reason": "No face detected",
                }
            
            if len(faces) > 1:
                return {
                    "path": str(img_path),
                    "status": "no_face",
                    "reason": f"Multiple faces detected: {len(faces)}",
                }
            
            face = faces[0]
            
            # Координаты
            x1, y1, x2, y2 = face.bbox.astype(int)
            w, h = x2 - x1, y2 - y1
            
            # Качество (используем выравненный crop для согласованности с инвентаризацией)
            crop = face_align.norm_crop(img, face.kps).copy()
            quality = calculate_composite_quality(crop, face.bbox, face.kps, (img.shape[1], img.shape[0]))
            
            # Эмбеддинги
            emb_color = face.normed_embedding
            emb_bw = self.app.models['recognition'].get_feat(
                face_align.norm_crop(full_bw, face.kps)
            ).flatten()
            emb_bw /= np.linalg.norm(emb_bw)
            
            # Критерии отсева
            if h < 60 or w < 60:
                return {
                    "path": str(img_path),
                    "status": "too_small",
                    "reason": f"Face too small: {w}x{h}px",
                    "metrics": {"quality_score": quality["quality_score"]},
                }
            
            if quality["blur_score"] < 0.25:
                return {
                    "path": str(img_path),
                    "status": "blurred",
                    "reason": f"Blur too high: {1-quality['blur_score']:.1%}",
                    "metrics": {"quality_score": quality["quality_score"], "blur_score": quality["blur_score"]},
                }
            
            if quality["quality_score"] < 0.5:
                return {
                    "path": str(img_path),
                    "status": "rejected",
                    "reason": f"Quality too low: {quality['quality_score']:.2f}",
                    "metrics": {"quality_score": quality["quality_score"]},
                }
            
            return {
                "path": str(img_path),
                "status": "passed",
                "bbox": [float(x1), float(y1), float(w), float(h)],
                "metrics": {
                    "quality_score": quality["quality_score"],
                    "blur_score": quality["blur_score"],
                    "face_size": f"{w}x{h}",
                },
                "emb_color": emb_color,
                "emb_bw": emb_bw,
            }
            
        except Exception as e:
            return {
                "path": str(img_path),
                "status": "error",
                "reason": str(e),
            }
    
    def _deduplicate(self, embeddings: List[Dict], threshold: float = None) -> Tuple[List[Dict], Dict]:
        """Дедупликация по косинусу"""
        if threshold is None:
            threshold = DEFAULT_CONFIG.get("similarity_cross", 0.45) + 0.5  # 0.95 default
        if len(embeddings) == 0:
            return [], {}
        
        # Извлечение эмбеддингов
        color_embs = np.array([e["emb_color"] for e in embeddings])
        color_embs = color_embs / (np.linalg.norm(color_embs, axis=1, keepdims=True) + 1e-8)
        
        similarities = color_embs @ color_embs.T
        
        # Жадная дедупликация
        to_remove = set()
        mapping = {}
        
        for i in range(len(embeddings)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(embeddings)):
                if j in to_remove:
                    continue
                if similarities[i, j] > threshold:
                    to_remove.add(j)
                    mapping[j] = i
        
        # Оставляем только уникальные
        unique = [e for i, e in enumerate(embeddings) if i not in to_remove]
        mapping = {i: mapping.get(i, i) for i in range(len(embeddings)) if i not in to_remove}
        
        return unique, mapping
    
    def _select_diverse(self, embeddings: List[Dict], max_count: int = 8) -> List[Dict]:
        """
        Выбрать разнообразные фото (разные ракурсы/свет)
        
        Использует diversity scoring по углам поворота и качеству
        """
        if len(embeddings) <= max_count:
            return embeddings
        
        # Сортировка по качеству
        sorted_embs = sorted(embeddings, key=lambda e: e["metrics"]["quality_score"], reverse=True)
        
        # Выбор лучших с учетом диверситета
        selected = [sorted_embs[0]]
        
        for emb in sorted_embs[1:max_count]:
            # Проверка на близость к уже выбранным
            is_diverse = True
            for sel in selected:
                sim = float(np.dot(emb["emb_color"], sel["emb_color"]))
                if sim > 0.85:  # слишком похоже
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(emb)
        
        # Если мало диверситета, добавляем больше
        while len(selected) < max_count and len(selected) < len(sorted_embs):
            for emb in sorted_embs:
                if emb not in selected:
                    selected.append(emb)
                    break
        
        return selected[:max_count]
    
    def check_similar_in_db(self, embedding: np.ndarray, threshold: float = None) -> Optional[Dict]:
        """
        Проверить похожесть на существующих в БД
        
        Returns:
            dict с найденной персоной или None
        """
        if threshold is None:
            threshold = DEFAULT_CONFIG.get("similarity_intra", 0.55)
        if self.prisma is None:
            return None
        
        # Получить всех людей с эмбеддингами
        persons = self.prisma.person.find_many(
            where={"embedding_count": {"gt": 0}},
            include={"descriptors": True}
        )
        
        for person in persons:
            for desc in person.descriptors:
                db_emb = np.array(json.loads(desc.descriptor))
                sim = float(np.dot(embedding, db_emb))
                if sim > threshold:
                    return {
                        "person_id": person.id,
                        "person_name": person.name,
                        "similarity": sim,
                        "match_type": "exact",
                    }
        
        return None


def _convert_to_serializable(obj: Any) -> Any:
    """Преобразование numpy ndarray в list для JSON сериализации"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    return obj


# Пример использования
if __name__ == "__main__":
    pipeline = PersonIntakePipeline()
    
    result = pipeline.process_folder(
        r"D:\bd_gosti\test_dataset\modern_1080p",
        "Test Person"
    )
    
    print(json.dumps(result, indent=2, default=str))

# ============================================
# FastAPI Server for Intake Pipeline
# ============================================

def create_intake_app(prisma_client=None) -> "FastAPI":
    """
    Создание FastAPI приложения для intake endpoint
    
    Args:
        prisma_client: Prisma Client для доступа к БД
    
    Returns:
        FastAPI app instance
    """
    try:
        from fastapi import FastAPI, File, UploadFile, Form, HTTPException
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        from typing import Optional
        import tempfile
        import shutil
    except ImportError:
        raise RuntimeError("FastAPI is not installed. Install with: pip install fastapi uvicorn")
    
    app = FastAPI(title="Person Intake API")
    
    # Инициализация пайплайна (single instance)
    pipeline = PersonIntakePipeline(prisma_client)
    
    class IntakeRequest(BaseModel):
        folder: str
        person_id: Optional[int] = None
        person_name: Optional[str] = None
    
    @app.post("/intake")
    async def intake_folder(
        folder: str = Form(...),
        person_id: Optional[int] = Form(None),
        person_name: Optional[str] = Form(None)
    ):
        """
        Обработка папки с фото персонала
        
        Args:
            folder: путь к папке с фото
            person_id: ID существующей персоны (опционально)
            person_name: имя персоны (если person_id не указан)
        
        Returns:
            dict с результатами обработки
        """
        try:
            result = pipeline.process_folder(folder, person_name or "Unknown")
            # Преобразование ndarray в list для JSON сериализации
            result = _convert_to_serializable(result)
            return JSONResponse(content=result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/intake/single")
    async def intake_single_image(
        file: UploadFile = File(...),
        person_id: Optional[int] = Form(None),
        person_name: Optional[str] = Form(None)
    ):
        """
        Обработка одного изображения
        
        Args:
            file: uploaded image file
            person_id: ID существующей персоны
            person_name: имя персоны
        
        Returns:
            dict с результатами обработки одного фото
        """
        try:
            # Сохранить временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Обработать одно фото как папку
                folder_path = str(Path(tmp_path).parent)
                result = pipeline.process_folder(folder_path, person_name or "Unknown")
                
                # Вернуть только результат для этого файла
                if result.get("report") and len(result["report"]) > 0:
                    single_result = result["report"][0]
                    return JSONResponse(content={
                        "filename": file.filename,
                        **single_result
                    })
                else:
                    return JSONResponse(content={"error": "No result", "filename": file.filename})
            finally:
                Path(tmp_path).unlink(missing_ok=True)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


# Запуск сервера напрямую (для тестирования)
if __name__ == "__main__":
    import uvicorn
    
    # Попытка получить prisma client
    prisma = None
    try:
        from prisma import Prisma
        prisma = Prisma()
    except Exception as e:
        print(f"Could not initialize Prisma: {e}")
    
    app = create_intake_app(prisma)
    uvicorn.run(app, host="0.0.0.0", port=8001)
