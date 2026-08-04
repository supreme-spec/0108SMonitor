"""Test PersonIntakePipeline det with working test"""
import sys
sys.path.insert(0, 'backend')
from archive.intake import PersonIntakePipeline
from PIL import Image, ImageOps
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from pathlib import Path

img_path = r'test_dataset\enrollment\person1_photo1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

print(f'img shape: {img.shape}')

# Try different det_sizes with real image test
for det_size_val in [1280, 1024, 640]:
    app = FaceAnalysis(name='buffalo_l', root=r'backend\ai\models\models', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(det_size_val, det_size_val))
    faces = app.get(img)
    print(f'det_size={det_size_val}: Found {len(faces)} faces on real image')
