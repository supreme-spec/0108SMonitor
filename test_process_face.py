"""Test _process_face directly"""
import sys
sys.path.insert(0, 'backend')
from archive.processor import ArchiveProcessor
from PIL import Image, ImageOps
import numpy as np
import cv2

proc = ArchiveProcessor()

img_path = r'test_dataset\ep_ceiling_color\img1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

faces = proc.app.get(img)
print(f'Found {len(faces)} faces')

for i, face in enumerate(faces):
    print(f'Processing face {i}...')
    try:
        result = proc._process_face(face, img, i)
        print(f'  OK: bbox={result["bbox"]}, blur={result["blur_score"]:.3f}')
    except Exception as e:
        print(f'  ERROR: {type(e).__name__}: {e}')
        # Debug bbox
        x1, y1, x2, y2 = face.bbox.astype(int)
        print(f'    bbox: x1={x1}, y1={y1}, x2={x2}, y2={y2}')
        face_img = img[y1:y2, x1:x2]
        print(f'    face_img shape: {face_img.shape}, empty: {face_img.size == 0}')
