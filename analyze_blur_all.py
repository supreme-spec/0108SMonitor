"""Analyze blur_score for all enrollment photos"""
from backend.archive.quality import calculate_composite_quality
from PIL import Image, ImageOps
import cv2
import numpy as np
from insightface.app import FaceAnalysis

for name in ['person1_photo1.jpg', 'person2_photo1.jpg']:
    img_path = f'test_dataset/enrollment/{name}'
    pil = ImageOps.exif_transpose(Image.open(img_path))
    if pil.mode in ('CMYK', 'P', 'RGBA'):
        pil = pil.convert('RGB')
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(1024, 1024))
    faces = app.get(img)
    if faces:
        f = faces[0]
        x1, y1, x2, y2 = f.bbox.astype(int)
        crop = img[y1:y2, x1:x2].copy()
        q = calculate_composite_quality(crop, f.bbox, f.kps, (img.shape[1], img.shape[0]))
        print(f'{name}: blur_score={q["blur_score"]:.4f}, crop shape={crop.shape}')
    else:
        print(f'{name}: No faces detected')
