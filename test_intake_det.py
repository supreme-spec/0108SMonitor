"""Test PersonIntakePipeline det"""
import sys
sys.path.insert(0, 'backend')
from archive.intake import PersonIntakePipeline
from PIL import Image, ImageOps
import numpy as np
import cv2

pipeline = PersonIntakePipeline()

img_path = r'test_dataset\enrollment\person1_photo1.jpg'
pil_img = Image.open(img_path)
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

print(f'img shape: {img.shape}')

faces = pipeline.app.get(img)
print(f'Found {len(faces)} faces')
