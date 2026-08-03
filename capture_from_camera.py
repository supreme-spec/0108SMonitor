"""Capture single frame from camera and save it."""
import cv2
import os
from pathlib import Path


def capture_from_camera(output_path: str = "tests/images/entrance/camera_capture.jpg"):
    """Capture single frame from default camera."""
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print(f"ERROR: Could not open camera 0")
        print("Trying camera 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("ERROR: Could not open any camera")
            return None
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    print("Camera opened. Frame size: 1920x1080")
    print("Capturing frame in 3 seconds...")
    
    # Wait for camera to adjust
    import time
    time.sleep(3)
    
    # Capture frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("ERROR: Could not read frame")
        return None
    
    # Save frame
    cv2.imwrite(output_path, frame)
    print(f"Saved: {output_path}")
    print(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
    
    return output_path


if __name__ == "__main__":
    result = capture_from_camera()
    
    if result:
        print(f"\nSuccess! Image saved to: {result}")
        print("You can now run:")
        print("  python benchmark_detector.py -i tests/images")
    else:
        print("\nFailed to capture image.")
        print("Check if camera is connected and accessible.")
