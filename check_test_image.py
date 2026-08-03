"""Check test_face.jpg properties."""
import cv2
import os

image_path = "assets/test_face.jpg"

# Check file size
file_size = os.path.getsize(image_path)
print(f"File size: {file_size} bytes")

# Check image with cv2
img = cv2.imread(image_path)
if img is None:
    print("ERROR: Could not read image with cv2.imread()")
else:
    print(f"cv2.imread() succeeded:")
    print(f"  Shape: {img.shape}")
    print(f"  Dtype: {img.dtype}")
    print(f"  Min pixel value: {img.min()}")
    print(f"  Max pixel value: {img.max()}")

# Check with PIL
try:
    from PIL import Image
    pil_img = Image.open(image_path)
    print(f"PIL.Image.open():")
    print(f"  Size: {pil_img.size}")
    print(f"  Mode: {pil_img.mode}")
    print(f"  Format: {pil_img.format}")
except Exception as e:
    print(f"PIL ERROR: {e}")
