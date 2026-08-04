"""Test face0 kps"""
import sys
sys.path.insert(0, 'backend')
from archive.processor import ArchiveProcessor
from PIL import Image, ImageOps
import numpy as np
import cv2

proc = ArchiveProcessor()

img_path = r'test_dataset\ep_ceiling_color\img2.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

faces = proc.app.get(img)
print(f'Found {len(faces)} faces')

face = faces[0]
x1, y1, x2, y2 = face.bbox.astype(int)
face_img = img[y1:y2, x1:x2]

print(f'face.bbox: {face.bbox}')
print(f'x1={x1}, y1={y1}, x2={x2}, y2={y2}')
print(f'face_img shape: {face_img.shape}')
print(f'face.kps: {face.kps}')
print(f'face.kps shape: {face.kps.shape if hasattr(face.kps, "shape") else "N/A"}')

# Check if face_img is valid for cv2
print(f'face_img dtype: {face_img.dtype}')
print(f'face_img.flags.c_contiguous: {face_img.flags.c_contiguous}')
print(f'face_img.flags.f_contiguous: {face_img.flags.f_contiguous}')

# Try cv2.cvtColor
try:
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    print(f'cv2.cvtColor OK: gray.shape={gray.shape}')
except Exception as e:
    print(f'cv2.cvtColor ERROR: {type(e).__name__}: {e}')
