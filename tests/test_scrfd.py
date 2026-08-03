#!/usr/bin/env python3
"""
Test SCRFD detection pipeline with real image
"""

import asyncio
import sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai.detectors.scrfd import SCRFD


async def main():
    # Initialize detector
    print("Initializing SCRFD...")
    detector = SCRFD()
    await detector.initialize()
    
    # Load test image
    test_image_path = Path(__file__).parent.parent / "assets" / "test_face.jpg"
    if not test_image_path.exists():
        print(f"Test image not found: {test_image_path}")
        print("Creating simple test image...")
        # Create simple test image with 2 faces (rectangles)
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        img[:] = 128  # Gray background
        
        # Add "faces" - colored rectangles
        cv2.rectangle(img, (100, 100), (200, 200), (0, 128, 255), -1)  # Left face
        cv2.rectangle(img, (300, 150), (450, 300), (255, 128, 0), -1)  # Right face
        
        # Save test image
        test_image_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(img).save(test_image_path)
        print(f"Created test image: {test_image_path}")
    else:
        img = np.array(Image.open(test_image_path))
        print(f"Loaded test image: {test_image_path}")
    
    # Convert to bytes
    img_pil = Image.fromarray(img)
    from io import BytesIO
    buffer = BytesIO()
    img_pil.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()
    
    # Run detection
    print("\nRunning detection...")
    start_time = asyncio.get_event_loop().time()
    faces = await detector.detect_with_embedding(image_bytes)
    end_time = asyncio.get_event_loop().time()
    
    print(f"\n=== Detection Results ===")
    print(f"Faces detected: {len(faces)}")
    print(f"Time: {(end_time - start_time) * 1000:.2f} ms")
    
    # Draw results
    img_draw = img.copy()
    
    for i, face in enumerate(faces):
        bbox = face["bbox"]
        x1, y1, x2, y2 = [int(b) for b in bbox[:4]]
        
        # Draw bbox
        cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw confidence
        conf = face.get("det_score", 0)
        cv2.putText(img_draw, f"Face {i+1} ({conf:.2f})", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Print details
        print(f"\nFace {i+1}:")
        print(f"  BBox: [{x1}, {y1}, {x2}, {y2}]")
        print(f"  Confidence: {conf:.3f}")
        if "embedding" in face:
            print(f"  Embedding: {len(face['embedding'])} dims")
    
    # Save result
    output_path = Path(__file__).parent / "test_scrfd_result.jpg"
    Image.fromarray(img_draw).save(output_path)
    print(f"\nResult saved to: {output_path}")
    
    # Cleanup
    await detector.unload_models()
    
    return len(faces)


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nTest {'PASSED' if result > 0 else 'FAILED'}")
    sys.exit(0 if result > 0 else 1)
