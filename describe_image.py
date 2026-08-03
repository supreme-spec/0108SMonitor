"""Describe the test image content."""
import cv2
import numpy as np
from PIL import Image

img = cv2.imread("assets/test_face.jpg")
pil_img = Image.open("assets/test_face.jpg")

print(f"OpenCV: shape={img.shape}, dtype={img.dtype}")
print(f"PIL: size={pil_img.size}, mode={pil_img.format}")

# Check image statistics
print(f"Pixel min: {img.min()}, max: {img.max()}, mean: {img.mean():.2f}")

# Check if image is mostly one color (background)
unique_values = np.unique(img)
print(f"Unique pixel values: {len(unique_values)}")

# Try to detect if it's a grayscale image converted to RGB
if len(np.unique(img[:, :, 0])) == len(np.unique(img[:, :, 1])) == len(np.unique(img[:, :, 2])):
    print("Warning: All channels have similar content - might be grayscale image")
    
# Try to detect edges
edges = cv2.Canny(img, 100, 200)
print(f"Edge pixels: {np.count_nonzero(edges)} out of {edges.size} ({100*np.count_nonzero(edges)/edges.size:.2f}%)")

# Check if it's a selfie-style image (face in center)
h, w = img.shape[:2]
center_region = img[h//3:2*h//3, w//3:2*w//3]
print(f"Center region pixel mean: {center_region.mean():.2f}")
print(f"Full image pixel mean: {img.mean():.2f}")

# Check contrast
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
print(f"Contrast (hist non-zero bins): {np.count_nonzero(hist)}")
