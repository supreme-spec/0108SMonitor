"""Test face processing"""
from PIL import Image, ImageOps
import numpy as np
import cv2
from pathlib import Path
import sys
sys.path.insert(0, r'D:\AI_Libraries\insightface-master\insightface-master\python-package')
from insightface.app import FaceAnalysis
from backend.archive.quality import calculate_composite_quality

app = FaceAnalysis(name='buffalo_l', root=r'backend\ai\models\models')
app.prepare(ctx_id=0, det_size=(640, 640))

img_path = r'test_dataset\ep_ceiling_color\img1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

print(f'Image shape: {img.shape}')

faces = app.get(img)
print(f'Found {len(faces)} faces')

for i, face in enumerate(faces):
    x1, y1, x2, y2 = face.bbox.astype(int)
    w, h = x2 - x1, y2 - y1
    face_image = img[y1:y2, x1:x2]
    print(f'Face {i}: bbox=[{x1},{y1}]-[{x2},{y2}], w={w}, h={h}')
    print(f'  face_image shape={face_image.shape}, size={face_image.size}, empty={face_image.size==0}')
    print(f'  kps type: {type(face.kps)}, shape: {face.kps.shape if hasattr(face.kps, "shape") else "N/A"}')
    if face_image.size > 0:
        try:
            result = calculate_composite_quality(face_image, np.array([x1, y1, w, h]), face.kps, (img.shape[1], img.shape[0]))
            print(f'  quality OK: blur={result.get("blur_score"):.3f}')
        except Exception as e:
            print(f'  quality FAILED: {type(e).__name__}: {e}')
    else:
        print(f'  SKIPPED: empty face_image')
