"""
Face Quality Assessment Module

Метрики качества:
- размытие (Laplacian variance)
- яркость и контраст
- экспозиция
- поза (yaw/pitch/roll)
- окклюзия
- размер лица
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional


def calculate_blur_score(face_image: np.ndarray, method: str = "laplacian") -> float:
    """
    Оценка размытия лица
    
    Args:
        face_image: BGR изображение лица
        method: метод оценки ('laplacian', 'tenengrad', 'smd')
    
    Returns:
        float: score от 0.0 (очень размыто) до 1.0 (очень резкое)
    """
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    
    if method == "laplacian":
        # Variance of Laplacian
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Масштабо-инвариантная калибровка по перцентилям:
        # p10 ≈ 52 (10-й перцентиль на большом наборе)
        # p90 ≈ 1623 (90-й перцентиль)
        # Тогда blur_score = (fm - 52) / (1623 - 52) = (fm - 52) / 1571
        # blur_score >= 0.25 соответствует fm >= 445
        p10, p90 = 52.0, 1623.0
        score = min(1.0, max(0.0, (fm - p10) / (p90 - p10)))
    elif method == "tenengrad":
        # Tenengrad FocussMeasure
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        fm = np.sqrt(sobelx**2 + sobely**2).mean()
        score = min(1.0, max(0.0, (fm - 10) / 90))
    elif method == "smd":
        # Spatial Gradient Metric
        gray = gray.astype(np.float64)
        h, w = gray.shape
        smd = 0.0
        for i in range(h - 1):
            for j in range(w - 1):
                smd += abs(gray[i, j] - gray[i + 1, j]) + abs(gray[i, j] - gray[i, j + 1])
        smd /= (h * w)
        score = min(1.0, max(0.0, (smd - 20) / 80))
    else:
        score = 0.5
    
    return score


def calculate_exposure_score(face_image: np.ndarray) -> Dict[str, float]:
    """
    Оценка экспозиции
    
    Returns:
        dict with keys:
        - brightness: средняя яркость (0-255)
        - contrast: контраст (std яркости)
        - overexposed: доля пересвеченных пикселей
        - underexposed: доля недоэкспонированных пикселей
    """
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    
    brightness = float(gray.mean())
    contrast = float(gray.std())
    
    # Доля пересвеченных (близких к 255) и недоэкспонированных (близких к 0) пикселей
    overexposed = (gray > 230).mean()
    underexposed = (gray < 20).mean()
    
    # Оценка качества экспозиции (0-1)
    # Идеал: яркость ~120, контраст ~40, мало пересвета/тени
    brightness_score = 1.0 - abs(brightness - 120) / 120
    contrast_score = min(1.0, contrast / 50)
    exposure_score = min(1.0, max(0.0, 1.0 - overexposed - underexposed))
    
    return {
        "brightness": brightness,
        "contrast": contrast,
        "overexposed": float(overexposed),
        "underexposed": float(underexposed),
        "brightness_score": float(brightness_score),
        "contrast_score": float(contrast_score),
        "exposure_score": float(exposure_score),
    }


def estimate_pose(landmarks: np.ndarray) -> Dict[str, float]:
    """
    Оценка угла поворота головы по 5 landmarks
    
    Args:
        landmarks: array shape (5, 2) - [left_eye, right_eye, nose, left_mouth, right_mouth]
    
    Returns:
        dict with yaw, pitch, roll in degrees
    """
    if landmarks.shape != (5, 2):
        return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "score": 0.0}
    
    # Простая оценка по положению глаз и носа
    left_eye = landmarks[0]
    right_eye = landmarks[1]
    nose = landmarks[2]
    
    # Угол между глазами (ROLL)
    eye_vector = right_eye - left_eye
    roll = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
    
    # Pitch и Yaw по положению носа относительно центра глаз
    eye_center = (left_eye + right_eye) / 2
    nose_to_center = nose - eye_center
    
    # Нормализация
    eye_distance = np.linalg.norm(eye_vector)
    if eye_distance < 1:
        return {"yaw": 0.0, "pitch": 0.0, "roll": float(roll), "score": 0.0}
    
    # Yaw: смещение носа влево/вправо
    yaw = np.degrees(np.arctan2(nose_to_center[0], eye_distance * 0.5))
    
    # Pitch: смещение носа вверх/вниз
    pitch = np.degrees(np.arctan2(nose_to_center[1], eye_distance * 0.3))
    
    # Качество оценки (0-1)
    score = 1.0 - min(abs(yaw), 90) / 90 - min(abs(pitch), 45) / 45
    score = max(0.0, min(1.0, score))
    
    return {
        "yaw": float(yaw),
        "pitch": float(pitch),
        "roll": float(roll),
        "score": float(score),
    }


def calculate_face_size_score(bbox: np.ndarray, image_size: Tuple[int, int]) -> float:
    """
    Оценка размера лица относительно изображения
    
    Args:
        bbox: [x, y, w, h] bounding box
        image_size: (width, height) изображения
    
    Returns:
        float: score от 0.0 (очень маленькое) до 1.0 (оптимальный размер)
    """
    img_w, img_h = image_size
    x, y, w, h = bbox
    
    # Площадь лица
    face_area = w * h
    img_area = img_w * img_h
    face_ratio = face_area / img_area
    
    # Идеал: 0.04-0.15 (лицо занимает 4-15% изображения)
    if face_ratio < 0.01:
        score = 0.2  # слишком маленькое
    elif face_ratio < 0.04:
        score = 0.5 + 5 * face_ratio  # 0.2 -> 0.4
    elif face_ratio < 0.15:
        score = 0.9 - 2 * abs(face_ratio - 0.1)
    else:
        score = 0.9 - 5 * (face_ratio - 0.15)
    
    return max(0.0, min(1.0, score))


def estimate_occlusion(face_image: np.ndarray) -> Dict[str, float]:
    """
    Оценка окклюзии (маска, очки, волосы, рука)
    
    Returns:
        dict with occlusion_score and estimated_parts
    """
    # Простая эвристика по распределению яркости
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # Средняя яркость по трём зонам (верх, середина, низ)
    top_mean = gray[:h//3].mean()
    mid_mean = gray[h//3:2*h//3].mean()
    bot_mean = gray[2*h//3:].mean()
    
    # Если верхняя зона сильно темнее - возможно волосы/кепка
    top_dark = (top_mean < mid_mean * 0.7)
    # Если нижняя зона сильно темнее - возможно маска/шарф
    bot_dark = (bot_mean < mid_mean * 0.7)
    
    # Оценка по контрасту (низкий контраст = окклюзия)
    contrast = gray.std()
    contrast_score = min(1.0, contrast / 40)
    
    occlusion_score = 1.0 - 0.3 * (top_dark + bot_dark) - 0.4 * (1.0 - contrast_score)
    
    return {
        "occlusion_score": float(max(0.0, min(1.0, occlusion_score))),
        "top_dark": bool(top_dark),
        "bot_dark": bool(bot_dark),
        "contrast_score": float(contrast_score),
    }


def calculate_composite_quality(face_image: np.ndarray, 
                                bbox: np.ndarray, 
                                landmarks: Optional[np.ndarray] = None,
                                image_size: Tuple[int, int] = (1920, 1080)) -> Dict[str, any]:
    """
    Комплексная оценка качества лица
    
    Returns:
        dict with all quality metrics and overall score
    """
    result = {}
    
    # Размер лица
    result["face_size_score"] = calculate_face_size_score(bbox, image_size)
    
    # Размытие
    result["blur_score"] = calculate_blur_score(face_image)
    
    # Экспозиция
    exposure = calculate_exposure_score(face_image)
    result.update(exposure)
    
    # Поза
    if landmarks is not None:
        pose = estimate_pose(landmarks)
        result.update(pose)
    else:
        result["yaw"] = 0.0
        result["pitch"] = 0.0
        result["roll"] = 0.0
        result["pose_score"] = 0.5
    
    # Окклюзия
    occlusion = estimate_occlusion(face_image)
    result.update(occlusion)
    
    # Композитная оценка качества (0-1)
    # Веса: размытие 0.25, размер 0.20, экспозиция 0.20, поза 0.15, окклюзия 0.20
    weights = {
        "blur_score": 0.25,
        "face_size_score": 0.20,
        "exposure_score": 0.15,
        "contrast_score": 0.05,
        "pose_score": 0.15,
        "occlusion_score": 0.20,
    }
    
    # Составной score
    composite_score = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        if key in result:
            value = result[key]
            # Преобразование value в score 0-1
            if isinstance(value, bool):
                score = 1.0 if value else 0.0
            else:
                score = max(0.0, min(1.0, float(value)))
            composite_score += weight * score
            weight_sum += weight
    
    if weight_sum > 0:
        composite_score /= weight_sum
    
    result["quality_score"] = float(composite_score)
    
    # ТIER classification
    if composite_score >= 0.7:
        result["tier"] = "A"
    elif composite_score >= 0.4:
        result["tier"] = "B"
    elif composite_score >= 0.25:
        result["tier"] = "C"
    else:
        result["tier"] = "D"
    
    return result


# Пример использования
if __name__ == "__main__":
    # Пример теста
    test_img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    test_bbox = np.array([50, 50, 100, 100])
    test_landmarks = np.array([[80, 80], [120, 80], [100, 100], [85, 120], [115, 120]])
    
    result = calculate_composite_quality(test_img, test_bbox, test_landmarks)
    print("Quality assessment:", result)
