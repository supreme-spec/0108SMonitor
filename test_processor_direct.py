"""Test processor directly"""
from PIL import Image, ImageOps
import numpy as np
import cv2
from pathlib import Path
import sys
sys.path.insert(0, r'D:\AI_Libraries\insightface-master\insightface-master\python-package')
from insightface.app import FaceAnalysis

app = FaceAnalysis(name='buffalo_l', root=r'backend\ai\models\models')
app.prepare(ctx_id=-1, det_size=(1024, 1024))

img_path = r'test_dataset\ep_ceiling_color\img1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

faces = app.get(img)
print(f'Found {len(faces)} faces')

for i, face in enumerate(faces):
    x1, y1, x2, y2 = face.bbox.astype(int)
    print(f'Face {i}: bbox={face.bbox}')
    print(f'  x1={x1}, y1={y1}, x2={x2}, y2={y2}')
    face_img = img[y1:y2, x1:x2]
    print(f'  face_img shape: {face_img.shape}, empty: {face_img.size == 0}')
    # Попробуем calculate_composite_quality
    from backend.archive.quality import calculate_composite_quality
    try:
        result = calculate_composite_quality(face_img, np.array([x1, y1, x2-x1, y2-y1]), face.kps, (img.shape[1], img.shape[0]))
        print(f'  quality OK')
    except Exception as e:
        print(f'  quality ERROR: {type(e).__name__}: {e}')
