"""Test PersonIntakePipeline debug"""
import sys
sys.path.insert(0, 'backend')
from archive.intake import PersonIntakePipeline
from PIL import Image, ImageOps
import numpy as np
import cv2
from archive.quality import calculate_composite_quality

pipeline = PersonIntakePipeline()

img_path = r'test_dataset\enrollment\person1_photo1.jpg'

# Загрузка как в _process_single_image
pil_img = Image.open(img_path)
if pil_img.mode in ('CMYK', 'P', 'RGBA', 'LA'):
    pil_img = pil_img.convert('RGB')
pil_img = ImageOps.exif_transpose(pil_img)
img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
full_bw = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

faces = pipeline.app.get(img)
face = faces[0]

x1, y1, x2, y2 = face.bbox.astype(int)
w, h = x2 - x1, y2 - y1

print(f'face.bbox: {face.bbox}')
print(f'face.kps: {face.kps}')

crop = img[y1:y2, x1:x2]
print(f'crop shape: {crop.shape}')

quality = calculate_composite_quality(crop, face.bbox, face.kps, (img.shape[1], img.shape[0]))
print(f'quality: blur_score={quality["blur_score"]:.3f}, quality_score={quality["quality_score"]:.3f}')

# Check thresholds
print(f'blur_score < 0.3: {quality["blur_score"] < 0.3}')
print(f'quality_score < 0.5: {quality["quality_score"] < 0.5}')

# Check size
print(f'w < 60: {w < 60}, h < 60: {h < 60}')
