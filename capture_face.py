"""Capture face image from webcam for testing."""
import cv2
import os
from datetime import datetime

def capture_face(output_path="assets/captured_face.jpg"):
    """Capture a single frame from webcam and save it."""
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open webcam")
        return None
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("Webcam opened. Press SPACE to capture, ESC to exit.")
    print("Make sure your face is visible in the frame.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Could not read frame")
            break
        
        # Show frame
        cv2.imshow('Capture Face - Press SPACE to save, ESC to exit', frame)
        
        # Wait for key
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("Cancelled")
            break
        elif key == 32:  # SPACE
            # Save image
            cv2.imwrite(output_path, frame)
            print(f"Image saved to: {output_path}")
            print(f"Image size: {frame.shape[1]}x{frame.shape[0]}")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    return output_path if os.path.exists(output_path) else None

if __name__ == "__main__":
    # Create assets directory if not exists
    os.makedirs("assets", exist_ok=True)
    
    # Capture face
    result = capture_face()
    
    if result:
        print(f"\nSuccess! Captured image: {result}")
        print("You can now test face detection with this image.")
    else:
        print("\nFailed to capture image.")
