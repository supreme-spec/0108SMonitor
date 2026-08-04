#!/usr/bin/env python3
"""
Debug script to check image loading and face detection.
"""

import sys
import cv2
import numpy as np
from PIL import Image, ImageOps

# Добавляем пути к библиотекам
AI_LIBS_DIR = r"D:\AI_Libraries"
sys.path.insert(0, str(AI_LIBS_DIR + r"\insightface-master\insightface-master\python-package"))

from insightface.app import FaceAnalysis


def load_image(path):
    """Загрузить изображение с конвертацией CMYK/P/RGBA в RGB"""
    pil = Image.open(path)
    print(f'Original mode: {pil.mode}, size: {pil.size}')
    
    # EXIF транспозиция ПЕРВОЙ (до конвертации)
    pil = ImageOps.exif_transpose(pil)
    print(f'After exif_transpose: mode={pil.mode}, size={pil.size}')
    
    # Конвертация CMYK/P/RGBA в RGB
    if pil.mode in ('CMYK', 'P', 'RGBA', 'LA'):
        pil = pil.convert('RGB')
        print(f'Converted to RGB')
    
    arr = np.array(pil)
    print(f'Final shape: {arr.shape}, dtype={arr.dtype}')
    
    img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return img


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_one.py <image_path>")
        return
    
    img_path = sys.argv[1]
    
    print(f"Processing: {img_path}")
    print("-" * 50)
    
    img = load_image(img_path)
    print(f'Final image shape: {img.shape}, dtype: {img.dtype}')
    
    # Инициализация FaceAnalysis
    # Адаптивный det_size: 1024 -> 640 -> 1600
    img_h, img_w = img.shape[:2]
    max_dim = max(img_h, img_w)
    
    # Сначала пробуем 1024
    det_sizes = [1024, 640, 1600]
    
    for det_size_val in det_sizes:
        print(f"Trying det_size={det_size_val}...")
        app = FaceAnalysis(
            name='buffalo_l',
            root='backend/ai/models',
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        app.prepare(ctx_id=0, det_size=(det_size_val, det_size_val))
        
        faces = app.get(img)
        print(f'  Detected: {len(faces)} faces')
        
        if len(faces) > 0:
            print(f"Using det_size: {det_size_val}")
            break
        else:
            print(f"  No faces detected, trying next size...")
    
    if len(faces) == 0:
        print("Warning: No faces detected at any det_size")
    
    print("-" * 50)
    print("Face detection results:")
    
    faces = app.get(img)
    if len(faces) == 0:
        print("  NO FACES DETECTED")
    else:
        for i, f in enumerate(faces):
            print(f'  Face {i}: det={round(float(f.det_score), 3)}, bbox={f.bbox.astype(int)}')
    
    print("-" * 50)


if __name__ == '__main__':
    main()
