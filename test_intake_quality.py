"""Test PersonIntakePipeline quality"""
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
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
full_bw = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

faces = pipeline.app.get(img)
print(f'Found {len(faces)} faces')

for i, face in enumerate(faces):
    print(f'Face {i}: bbox={face.bbox}')
    x1, y1, x2, y2 = face.bbox.astype(int)
    crop = img[y1:y2, x1:x2]
    print(f'crop shape: {crop.shape}')
    
    from archive.quality import calculate_composite_quality
    quality = calculate_composite_quality(crop, face.bbox, face.kps, (img.shape[1], img.shape[0]))
    print(f'quality: blur_score={quality["blur_score"]:.3f}, quality_score={quality["quality_score"]:.3f}')
