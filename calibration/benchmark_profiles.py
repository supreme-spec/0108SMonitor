#!/usr/bin/env python3
"""
Calibration Benchmark for Source Profiles

Измеряет характеристики фото из разных профилей источника:
- modern_1080p
- color_lowres
- ir_screen_photo

Выводит CSV с метриками для подбора порогов тиров A/B/C/D и T_INTRA
"""

import argparse
import csv
import itertools
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps

# Добавляем пути к библиотекам
AI_LIBS_DIR = Path(r"D:\AI_Libraries")
import sys
sys.path.insert(0, str(AI_LIBS_DIR / "insightface-master" / "insightface-master" / "python-package"))

from insightface.app import FaceAnalysis
from insightface.utils import face_align


def load_image(path: Path) -> np.ndarray:
    """Загрузить изображение с конвертацией CMYK/P/RGBA в RGB"""
    pil = Image.open(path)
    
    # Конвертация CMYK/P/RGBA/LA в RGB
    if pil.mode in ('CMYK', 'P', 'RGBA', 'LA'):
        pil = pil.convert('RGB')
    
    pil = ImageOps.exif_transpose(pil)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def calculate_quality_metrics(face_image: np.ndarray, bbox: np.ndarray) -> dict:
    """
    Рассчитать метрики качества для кропа лица
    """
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    h, w = face_image.shape[:2]
    
    # Размытие (Laplacian variance)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # Яркость и контраст
    brightness = float(gray.mean())
    contrast = float(gray.std())
    
    # Размер лица
    x1, y1, x2, y2 = bbox.astype(int)
    face_w, face_h = x2 - x1, y2 - y1
    
    return {
        "blur": blur,
        "brightness": brightness,
        "contrast": contrast,
        "face_w": face_w,
        "face_h": face_h,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dataset', help='корень с папками-профилями/эпизодами')
    ap.add_argument('--out', default='calibration/out')
    ap.add_argument('--models-root', default='backend/ai/models')
    ap.add_argument('--det-size', type=int, default=None)  # None = auto-detect
    ap.add_argument('--min-det', type=float, default=0.3)
    a = ap.parse_args()
    
    # Инициализация FaceAnalysis с адаптивным det_size
    app = FaceAnalysis(
        name='buffalo_l',
        root=a.models_root,
        providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
    )
    
    # Адаптивный det_size: 1024 -> 640 -> 1600
    det_sizes = [1024, 640, 1600]
    if a.det_size is not None:
        det_sizes = [a.det_size]
    
    print(f"Trying det_sizes: {det_sizes}")
    faces_test = None
    for det_size_val in det_sizes:
        app.prepare(ctx_id=0, det_size=(det_size_val, det_size_val))
        # Пробный прогон на первом изображении (если есть)
        dataset_path = Path(a.dataset)
        if dataset_path.exists():
            first_folder = next((p for p in dataset_path.iterdir() if p.is_dir()), None)
            if first_folder:
                first_img = next((p for p in first_folder.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png')), None)
                if first_img:
                    try:
                        test_img = load_image(first_img)
                        faces_test = app.get(test_img)
                        if len(faces_test) > 0:
                            print(f"Using det_size: {det_size_val} (found {len(faces_test)} faces)")
                            break
                        else:
                            print(f"  det_size={det_size_val}: no faces")
                    except Exception as e:
                        print(f"  det_size={det_size_val}: error - {e}")
    
    if len(faces_test) == 0 and len(det_sizes) > 1:
        # Если ни один det_size не сработал, используем последний
        print(f"Warning: No faces detected, using det_size={det_sizes[-1]}")
    
    rec = app.models['recognition']
    
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    
    faces_rows, pairs_rows = [], []
    
    # Обработка папок
    dataset_path = Path(a.dataset)
    if not dataset_path.exists():
        print(f"Dataset not found: {a.dataset}")
        return
    
    for folder in sorted(p for p in dataset_path.iterdir() if p.is_dir()):
        print(f"Processing {folder.name}...")
        embs = []
        
        imgs = sorted(p for p in folder.iterdir()
                      if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
        
        if not imgs:
            print(f"  No images in {folder.name}")
            continue
        
        for ip in imgs:
            try:
                img = load_image(ip)
                
                # Полночёрное копия для ч/б-близнеца
                full_bw = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
                
                # Детекция
                faces = app.get(img)
                
                for fi, f in enumerate(faces):
                    if f.det_score < a.min_det:
                        continue
                    
                    x1, y1, x2, y2 = f.bbox.astype(int)
                    
                    # Кроп с выравниванием
                    crop = face_align.norm_crop(img, f.kps)
                    crop_bw = face_align.norm_crop(full_bw, f.kps)
                    
                    # Эмбеддинги
                    emb = f.normed_embedding
                    eb = rec.get_feat(crop_bw).flatten()
                    eb /= np.linalg.norm(eb)
                    
                    # Дельта цвет-ч/б
                    gap = float(np.dot(emb, eb))
                    
                    # Метрики качества
                    metrics = calculate_quality_metrics(crop, f.bbox)
                    
                    # Сохранение кропа
                    crop_path = out / f'{folder.name}_{ip.stem}_f{fi}.jpg'
                    cv2.imwrite(str(crop_path), crop)
                    
                    faces_rows.append([
                        folder.name,
                        ip.name,
                        fi,
                        round(float(f.det_score), 3),
                        x2 - x1,
                        y2 - y1,
                        round(metrics["blur"], 1),
                        round(metrics["brightness"], 1),
                        round(gap, 3),
                    ])
                    
                    embs.append((ip.name, fi, emb))
                    
            except Exception as e:
                print(f"  Error processing {ip}: {e}")
                continue
        
        # Подсчёт похожестей между лицами
        for (na, fa, ea), (nb, fb, eb) in itertools.combinations(embs, 2):
            s = float(np.dot(ea, eb))
            if s > 0.25:
                pairs_rows.append([folder.name, f'{na}#{fa}', f'{nb}#{fb}', round(s, 3)])
    
    # Сортировка и сохранение
    with open(out / 'faces.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'folder', 'img', 'face', 'det_score', 'w', 'h',
            'blur', 'brightness', 'color_vs_bw_self'
        ])
        w.writerows(faces_rows)
    
    with open(out / 'pairs.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['folder', 'a', 'b', 'cos'])
        w.writerows(pairs_rows)
    
    print(f'\nResults saved to {out}')
    print(f'faces: {len(faces_rows)}')
    print(f'pairs>0.25: {len(pairs_rows)}')
    
    # Сводка по папкам
    print('\nSummary by folder:')
    folders = {}
    for row in faces_rows:
        fold = row[0]
        if fold not in folders:
            folders[fold] = {'count': 0, 'blur': [], 'size': []}
        folders[fold]['count'] += 1
        folders[fold]['blur'].append(row[6])
        folders[fold]['size'].append(max(row[4], row[5]))
    
    for fold, data in folders.items():
        avg_blur = sum(data['blur']) / len(data['blur'])
        avg_size = sum(data['size']) / len(data['size'])
        print(f"  {fold}: {data['count']} faces, avg_blur={avg_blur:.1f}, avg_size={avg_size:.0f}px")


if __name__ == '__main__':
    main()
