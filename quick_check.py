import cv2
import os

print(f'File size: {os.path.getsize("assets/test_face.jpg")} bytes')
img = cv2.imread("assets/test_face.jpg")
print(f'cv2: shape={img.shape if img is not None else None}')
from PIL import Image
pil = Image.open("assets/test_face.jpg")
print(f'PIL: size={pil.size}, mode={pil.mode}')
