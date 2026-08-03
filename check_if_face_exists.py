"""Check if there's a face in the test image using a simple method."""
import cv2
import numpy as np

img = cv2.imread("assets/test_face.jpg")
print(f"Image shape: {img.shape}")
print(f"Image dtype: {img.dtype}")

# Try to detect face using OpenCV HAAR cascade (pre-trained, simple)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

print(f"HAAR faces detected: {len(faces)}")

for (x, y, w, h) in faces:
    print(f"Face at ({x}, {y}) with size {w}x{h}")
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

# Save result
cv2.imwrite("assets/test_face_haar_result.jpg", img)
print("Result saved to assets/test_face_haar_result.jpg")
