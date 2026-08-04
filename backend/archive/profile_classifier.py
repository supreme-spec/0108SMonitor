"""
Source Profile Classifier

Автоматическое определение типа источника изображения:
- modern_1080p: современные камеры, высокое разрешение, цвет
- color_lowres: старые цветные камеры, низкое разрешение
- ir_screen_photo: ИК/пересъёмки с монитора
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List


def classify_source_profile(folder: Path) -> str:
    """
    Классифицировать источник по признакам папки
    
    Args:
        folder: путь к папке с фото
    
    Returns:
        имя профиля ('modern_1080p', 'color_lowres', 'ir_screen_photo')
    """
    # Получаем несколько случайных фото
    image_files = [
        f for f in folder.iterdir()
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
    ][:5]
    
    if not image_files:
        return "modern_1080p"  # дефолт
    
    features = {
        "avg_resolution": 0,
        "is_color": True,
        "has_osd": False,
        "has_moire": False,
        "avg_brightness": 128,
    }
    
    resolutions = []
    
    for img_path in image_files:
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            height, width = img.shape[:2]
            resolutions.append((width, height))
            
            # Цветное или монохромное
            if len(img.shape) == 2:
                features["is_color"] = False
            else:
                # Проверяем на ИК (зеленоватый оттенок в grayscale)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                b, g, r = cv2.split(img)
                # Если G >> R и G >> B - возможно ИК
                green_ratio = g.mean() / (r.mean() + 1e-6)
                if green_ratio > 1.5:
                    features["is_color"] = False
            
            # OSD текст
            if has_osd_text(img):
                features["has_osd"] = True
            
            # Муар (периодический узор)
            if has_moire_pattern(img):
                features["has_moire"] = True
            
            # Средняя яркость
            features["avg_brightness"] += img.mean()
            
        except Exception:
            continue
    
    if len(resolutions) == 0:
        return "modern_1080p"
    
    # Средняя резолюция
    avg_w = sum(r[0] for r in resolutions) / len(resolutions)
    avg_h = sum(r[1] for r in resolutions) / len(resolutions)
    features["avg_resolution"] = avg_w * avg_h
    features["avg_brightness"] /= len(image_files)
    
    # Классификация
    return _classify_by_features(features)


def _classify_by_features(features: Dict) -> str:
    """Классифицировать по признакам"""
    #modern_1080p: width >= 1280 and height >= 720 and is_color and not has_moire
    #color_lowres: width < 1280 and height < 720 and is_color
    #ir_screen_photo: not is_color or has_moire
    
    avg_res = features["avg_resolution"]
    is_color = features["is_color"]
    has_osd = features["has_osd"]
    has_moire = features["has_moire"]
    
    # ИК или муар = ir_screen_photo
    if not is_color or has_moire:
        return "ir_screen_photo"
    
    # Высокое разрешение + цвет = modern_1080p
    if avg_res >= 1280 * 720:
        return "modern_1080p"
    
    # Низкое разрешение + цвет = color_lowres
    return "color_lowres"


def has_osd_text(img: np.ndarray, threshold: float = 0.1) -> bool:
    """
    Проверить наличие OSD текста (большие блоки однородного текста)
    
    Returns:
        True если обнаружен OSD
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Простая детекция крупных блоков текста
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Ищем контуры крупных прямоугольников
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect = w / h if h > 0 else 0
        
        # ОSD обычно: большая площадь, узкий прямоугольник (верхняя полоса)
        if area > gray.shape[0] * gray.shape[1] * 0.05:  # >5% картинки
            if aspect > 3 or aspect < 0.3:  # узкий
                return True
    
    return False


def has_moire_pattern(img: np.ndarray) -> bool:
    """
    Проверить наличие муара (периодический узор от пересъёмки монитора)
    
    Returns:
        True если обнаружен муар
    """
    # Переводим в grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Фурье-спектр
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.log(np.abs(f_shift) + 1)
    
    # Ищем пиковую активность на средних частотах (муар)
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    
    # Кольцо средних частот
    inner_r, outer_r = min(h, w) // 8, min(h, w) // 4
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - center_w)**2 + (y - center_h)**2)
    
    ring_mask = (dist_from_center >= inner_r) & (dist_from_center <= outer_r)
    
    if ring_mask.sum() == 0:
        return False
    
    ring_mean = magnitude[ring_mask].mean()
    full_mean = magnitude.mean()
    
    # Если средняя активность в кольце значительно выше средней по картинке - муар
    return ring_mean > full_mean * 1.5


# Пример использования
if __name__ == "__main__":
    folder = Path(r"D:\bd_gosti\test_dataset\ceiling")
    profile = classify_source_profile(folder)
    print(f"Detected profile: {profile}")
