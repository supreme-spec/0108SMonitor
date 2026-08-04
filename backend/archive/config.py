"""
Archive Processor Configuration

Глобальные настройки, профили обработки и границы тиров.
"""

import os
from pathlib import Path

# Пути к библиотекам AI
AI_LIBS_DIR = Path(r"D:\AI_Libraries")
INSIGHTFACE_DIR = AI_LIBS_DIR / "insightface-master" / "insightface-master"
ADAFACE_DIR = AI_LIBS_DIR / "AdaFace-master" / "AdaFace-master"
ARCFACE_DIR = AI_LIBS_DIR / "ArcFace-main" / "ArcFace-main"
RETINAFACE_DIR = AI_LIBS_DIR / "retinaface-master" / "retinaface-master"
YOLOFACE_DIR = AI_LIBS_DIR / "yolo-face-dev" / "yolo-face-dev"
FAISS_DIR = AI_LIBS_DIR / "faiss-main" / "faiss-main"
ORT_GPU_DIR = AI_LIBS_DIR / "onnxruntime-win-x64-gpu_cuda12-1.28.0"
ORT_CPU_DIR = AI_LIBS_DIR / "onnxruntime-win-arm64-1.28.0"

# Пути к моделям в проекте
PROJECT_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_DIR / "backend" / "ai" / "models"
DATABASE_DIR = PROJECT_DIR / "backend" / "ai" / "database"

# FACE_API_KEY для вызова /update-index (из .env)
FACE_API_KEY = os.getenv("FACE_API_KEY", "")

# ============= GLOBAL CONFIG =============
# Глобальные пороги для всех профилей
GLOBAL = {
    # косинус для cross-camera merge только через operator
    "t_cross": 0.45,
    
    # порог дедупликации внутри одной персоны (фото одной сессии)
    "dedup_same_photo": 0.95,
    
    # "похож на другого" при зачислении нового персонала
    "cross_person_alert": 0.60,
    
    # серая зона: не авто-merge, не авто-отклонение (для manual review)
    "gray_zone": (0.25, 0.45),
    
    # тип кластеризации: 'union_find' или 'centroid'
    "clustering": "union_find",
}


# ============= TIERS =============
# Глобальные границы тиров качества
# Если use_blur=True в профиле, используется blur, иначе только w+bright+det
TIERS = {
    "A": {
        "w": 90,           # мин. размер лица
        "blur": 100,       # мин. variance Laplacian
        "bright": (50, 200),  # диапазон яркости
        "det": 0.7,        # мин. det_score
    },
    "B": {
        "w": 60,
        "blur": 40,
        "bright": (40, 220),
        "det": 0.6,
    },
    "C": {
        "w": 40,
        "blur": 0,         # blur не контролируется
        "bright": (20, 240),
        "det": 0.5,
    },
    # D — всё остальное (ручной контроль)
}


# ============= PROFILES =============
# Профили обработки по типу источника
# Каждый профиль может переопределять глобальные настройки
PROFILES = {
    # ==================== enrollment ====================
    "enrollment": {
        "description": "Фото персонала (эталон)",
        "detector": "scrfd",
        "recognizer": "arcface",
        "min_face_size": 200,     # большие лица для эталона
        
        # det_sizes по умолчанию (адаптивный: если 0 лиц -> 640 -> 1600)
        "det_sizes": (1024, 640),
        "min_det": 0.5,
        
        # для качества
        "auto_match": None,  # эталон не матчим, только зачисляем
    },
    
    # ==================== modern_osd ====================
    "modern_osd": {
        "description": "Современные камеры 1080p+ с OSD",
        "detector": "scrfd",
        "recognizer": "arcface",
        "min_face_size": 50,
        
        # det_sizes по умолчанию
        "det_sizes": (1024,),
        "min_det": 0.6,
        
        # кластеризация
        "t_intra": 0.50,           # порог внутри-персона
        "auto_match_sim": 0.55,    # порог для авто-матча с БД (только tier A/B)
        
        # качество
        "use_blur": True,          # использовать Laplacian blur
    },
    
    # ==================== ceiling_color ====================
    "ceiling_color": {
        "description": "Потолочные цветные камеры",
        "detector": "scrfd",
        "recognizer": "arcface",
        "min_face_size": 60,
        
        # det_sizes для потолочных камер (адаптивный)
        "det_sizes": (1024, 640),
        "min_det": 0.55,
        
        # кластеризация
        "t_intra": 0.40,           # ниже порог для потолочных (лица маленькие)
        "auto_match_sim": 0.45,    # авто-матч только с подтверждением
        
        # качество
        "use_blur": True,
    },
    
    # ==================== ir_screen ====================
    "ir_screen": {
        "description": "ИК/пересъёмки с монитора",
        "detector": "scrfd",
        "recognizer": "adaface",   # AdaFace для низкого качества
        "min_face_size": 40,
        
        # det_sizes
        "det_sizes": (1024, 640),
        "min_det": 0.5,
        
        # кластеризация
        "t_intra": 0.35,           # низкий порог (много разнообразия)
        "auto_match_sim": None,    # только ручная очередь (нет авто-матча)
        
        # качество
        "use_blur": False,         # Лапласиан на муаре/пересъёмке не работает
    },
}


# ============= DEFAULT_CONFIG =============
# Для обратной совместимости (старый код)
DEFAULT_CONFIG = {
    "min_face_size": 60,
    "min_det_score": 0.5,
    "pose_pitch_max": 35.0,
    "pose_yaw_max": 35.0,
    "quality_tier_a": 0.7,
    "quality_tier_b": 0.4,
    "similarity_intra": 0.55,
    "similarity_cross": 0.45,
    "use_multitemplate": True,
    "use_bw_twin": True,
    "max_photos_per_person": 15,
}


def get_model_paths(profile: str = "modern_osd") -> dict:
    """Получить пути к моделям для заданного профиля"""
    models = {
        "detector": None,
        "recognizer": None,
        "recognizer_bw": None,
    }
    
    profile_config = PROFILES.get(profile, PROFILES.get("modern_osd"))
    
    if profile_config.get("recognizer") == "adaface":
        # AdaFace для ИК и низкого качества
        models["recognizer"] = ADAFACE_DIR / "models" / "adaface_irn_se_r100.onnx"
        models["recognizer_bw"] = ADAFACE_DIR / "models" / "adaface_irn_se_r100_bw.onnx"
        models["detector"] = MODELS_DIR / "models" / "buffalo_l" / "det_10g.onnx"
    else:
        # ArcFace Buffalo L (по умолчанию)
        models["recognizer"] = MODELS_DIR / "models" / "buffalo_l" / "w600k_r50.onnx"
        models["detector"] = MODELS_DIR / "models" / "buffalo_l" / "det_10g.onnx"
    
    return models


def get_ai_lib_paths() -> dict:
    """Получить пути к библиотекам AI для импорта"""
    paths = {
        "insightface": INSIGHTFACE_DIR / "python-package",
        "adaface": ADAFACE_DIR,
        "arcface": ARCFACE_DIR,
        "retinaface": RETINAFACE_DIR,
        "yoloface": YOLOFACE_DIR,
        "faiss": FAISS_DIR,
    }
    return paths
