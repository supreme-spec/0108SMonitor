"""Test app.get() directly"""
import sys
sys.path.insert(0, 'backend')
from archive.processor import ArchiveProcessor

proc = ArchiveProcessor()

# Load image like in _process_image
from PIL import Image, ImageOps
import numpy as np
import cv2

img_path = r'test_dataset\ep_ceiling_color\img1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

print(f'img shape: {img.shape}')

faces = proc.app.get(img)
print(f'Found {len(faces)} faces')
for i, face in enumerate(faces):
    print(f'Face {i}: bbox={face.bbox}, type={type(face.bbox)}, dtype={face.bbox.dtype}')
