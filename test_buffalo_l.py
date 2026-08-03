"""Minimal test for buffalo_l model outside of project context."""
import sys
import cv2
import numpy as np

try:
    from insightface.app import FaceAnalysis
except ImportError as e:
    print(f"Failed to import insightface: {e}")
    sys.exit(1)

# 1. Load model
print("=" * 60)
print("STEP 1: Loading buffalo_l model...")
print("=" * 60)

try:
    app = FaceAnalysis(name="buffalo_l", root="backend/ai/models/models")
    app.prepare(ctx_id=-1, det_size=(640, 640))
    print("✓ buffalo_l model loaded successfully")
except Exception as e:
    print(f"✗ Failed to load buffalo_l: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Load test image
print("\n" + "=" * 60)
print("STEP 2: Loading test image...")
print("=" * 60)

test_image_path = "assets/test_face.jpg"
try:
    img = cv2.imread(test_image_path)
    if img is None:
        print(f"✗ Failed to read image: {test_image_path}")
        sys.exit(1)
    print(f"✓ Image loaded: shape={img.shape}, dtype={img.dtype}")
    print(f"  Image size: {img.shape[1]}x{img.shape[0]} pixels")
except Exception as e:
    print(f"✗ Failed to load image: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Detect faces
print("\n" + "=" * 60)
print("STEP 3: Detecting faces...")
print("=" * 60)

try:
    faces = app.get(img)
    print(f"✓ Detection completed: found {len(faces)} face(s)")
    
    if len(faces) > 0:
        print("\nFace details:")
        for i, face in enumerate(faces):
            print(f"  Face {i+1}:")
            print(f"    bbox: {face.bbox}")
            print(f"    kps: {face.kps}")
            print(f"    det_score: {face.det_score}")
            if hasattr(face, 'embedding'):
                print(f"    embedding shape: {face.embedding.shape}")
    else:
        print("\n⚠ WARNING: No faces detected!")
        print("This could be due to:")
        print("  - Poor image quality")
        print("  - Small face size")
        print("  - Bad lighting")
        print("  - Image not containing a face")
        
except Exception as e:
    print(f"✗ Detection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)
