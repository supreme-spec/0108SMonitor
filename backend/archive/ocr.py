"""
OSD Text Extraction

Извлечение текста OSD (наложенного на кадр камеры) для метаданных:
- дата/время съёмки
- ID камеры
- название места
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional


def extract_osd_text(img: np.ndarray) -> Optional[str]:
    """
    Извлечь текст OSD из изображения
    
    Args:
        img: BGR изображение
    
    Returns:
        распознанный текст или None
    """
    # Проверка наличия OSD в верхней/нижней полосе
    h, w = img.shape[:2]
    
    # Область OSD обычно 5-10% по вертикали
    top_osd = img[:int(h * 0.08), :]
    bottom_osd = img[-int(h * 0.08):, :]
    
    top_text = _extract_text_from_region(top_osd, "top")
    bottom_text = _extract_text_from_region(bottom_osd, "bottom")
    
    if top_text:
        return top_text
    if bottom_text:
        return bottom_text
    
    return None


def _extract_text_from_region(region: np.ndarray, position: str) -> Optional[str]:
    """Извлечь текст из заданной области"""
    # Конвертация в grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    
    # Бинаризация
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Поиск контуров
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Фильтрация контуров по размеру (текст usually large blocks)
    text_regions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect = w / h if h > 0 else 0
        
        # Текст: moderate area, not too thin
        if area > 100 and 0.2 < aspect < 5:
            text_regions.append((x, y, w, h))
    
    if len(text_regions) < 3:
        return None  # Нет достаточного количества текстовых блоков
    
    # Сортировка и объединение
    text_regions.sort(key=lambda r: (r[1] // 10, r[0]))  # по строкам
    
    # Простая эвристика: если есть много текстовых блоков в полосе - это OSD
    return _build_osd_string(text_regions, region, position)


def _build_osd_string(regions: list, region: np.ndarray, position: str) -> Optional[str]:
    """Построить OSD строку из найденных регионов"""
    # Простая строка для отладки
    # В реальном проекте здесь нужно использовать OCR (pytesseract, easyocr)
    
    osd_parts = []
    
    for i, (x, y, w, h) in enumerate(regions[:20]):  # максимум 20 блоков
        # Простая эвристика для извлечения даты/времени
        if h > 10:  # достаточно крупный
            osd_parts.append(f"[{x}:{y} {w}x{h}]")
    
    if osd_parts:
        return f"OSD_{position}_{'_'.join(osd_parts[:3])}"
    
    return None


def extract_timestamp(osd_text: str) -> Optional[str]:
    """
    Извлечь timestamp из OSD текста
    
    Поддерживает форматы:
    - YYYY-MM-DD HH:MM:SS
    - MM/DD/YYYY HH:MM:SS
    - DD.MM.YYYY HH:MM:SS
    """
    import re
    
    patterns = [
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{2}:\d{2}:\d{2})',  # только время
    ]
    
    for pattern in patterns:
        match = re.search(pattern, osd_text)
        if match:
            return match.group(1)
    
    return None


def extract_camera_id(osd_text: str) -> Optional[str]:
    """Извлечь ID камеры из OSD текста"""
    import re
    
    patterns = [
        r'([A-Z]{2,4}\d{4,6})',  # AURORA-V1, HIKVISION123
        r'(CAM\d{1,3})',  # CAM1, CAM123
        r'(CAMERA_\d+)',  # CAMERA_001
    ]
    
    for pattern in patterns:
        match = re.search(pattern, osd_text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


# Пример использования
if __name__ == "__main__":
    # Тест с пустым изображением
    test_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    result = extract_osd_text(test_img)
    print(f"OSD text: {result}")
