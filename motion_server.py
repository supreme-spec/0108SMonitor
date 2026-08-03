#!/usr/bin/env python3
"""
Motion Detection Server (FastAPI + OpenCV)
Реализует детекцию движения в зонах интереса (ROI) для камер.
"""

import asyncio
import os
import sys
import json
import logging
import time
import threading
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ─── Configuration ────────────────────────────────────────────────────────────

MOTION_THRESHOLD: float = float(os.getenv("MOTION_THRESHOLD", "0.62"))
MOTION_MIN_CONTOUR_AREA: int = int(os.getenv("MOTION_MIN_CONTOUR_AREA", "500"))
MOTION_HISTORY_LEN: int = int(os.getenv("MOTION_HISTORY_LEN", "16"))
MOTION_VAR_THRESHOLD: float = float(os.getenv("MOTION_VAR_THRESHOLD", "16"))
API_KEY: str = os.getenv("MOTION_API_KEY", "")

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="[MotionEngine] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_log_file = Path(__file__).parent / "logs" / "motion_server.log"
_log_file.parent.mkdir(exist_ok=True)
_file_handler = logging.FileHandler(_log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(_file_handler)

# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="Smart Security - Motion Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Global State ─────────────────────────────────────────────────────────────

motion_detectors: Dict[int, 'MotionDetector'] = {}
detectors_lock = threading.Lock()

# ─── Security Middleware ──────────────────────────────────────────────────────

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not API_KEY:
        return True
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# ─── Motion Detector Class ─────────────────────────────────────────────────────

class MotionDetector:
    """Детектор движения на основе MOG2."""
    
    def __init__(self, camera_id: int, threshold: float = MOTION_THRESHOLD):
        self.camera_id = camera_id
        self.threshold = threshold
        self.min_contour_area = MOTION_MIN_CONTOUR_AREA
        
        # MOG2 background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=MOTION_HISTORY_LEN,
            varThreshold=MOTION_VAR_THRESHOLD,
            detectShadows=True
        )
        
        # Zones of interest (ROI)
        self.zones: List[Dict[str, Any]] = []
        
        # Statistics
        self.motion_detected = False
        self.last_motion_time: Optional[float] = None
        self.motion_score = 0.0
        self.frame_count = 0
        
        logger.info(f"MotionDetector initialized for camera {camera_id}")
    
    def set_zones(self, zones: List[Dict[str, Any]]):
        """Установка зон детекции."""
        self.zones = zones
        logger.info(f"Zones updated for camera {self.camera_id}: {len(zones)} zones")
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Обработка кадра для детекции движения."""
        self.frame_count += 1
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Remove shadows
        _, fg_mask = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        motion_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        # Calculate motion score
        if motion_contours:
            total_area = sum(cv2.contourArea(c) for c in motion_contours)
            frame_area = frame.shape[0] * frame.shape[1]
            self.motion_score = min(total_area / frame_area, 1.0)
        else:
            self.motion_score = 0.0
        
        # Check if motion exceeds threshold
        motion_detected = self.motion_score > self.threshold
        
        if motion_detected:
            self.motion_detected = True
            self.last_motion_time = time.time()
        else:
            # Reset after 5 seconds of no motion
            if self.last_motion_time and time.time() - self.last_motion_time > 5:
                self.motion_detected = False
        
        # Zone-specific detection
        zone_results = []
        if self.zones:
            for zone in self.zones:
                zone_result = self._check_zone_motion(fg_mask, zone)
                zone_results.append(zone_result)
        
        return {
            "motion_detected": motion_detected,
            "motion_score": self.motion_score,
            "contour_count": len(motion_contours),
            "zone_results": zone_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_zone_motion(self, fg_mask: np.ndarray, zone: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка движения в конкретной зоне."""
        try:
            x1, y1, x2, y2 = zone['x1'], zone['y1'], zone['x2'], zone['y2']
            zone_mask = fg_mask[y1:y2, x1:x2]
            
            # Count white pixels in zone
            white_pixels = cv2.countNonZero(zone_mask)
            zone_area = (x2 - x1) * (y2 - y1)
            zone_motion_score = white_pixels / zone_area if zone_area > 0 else 0
            
            return {
                "zone_id": zone.get('id', 'unknown'),
                "zone_label": zone.get('label', 'unknown'),
                "motion_detected": zone_motion_score > self.threshold,
                "motion_score": zone_motion_score
            }
        except Exception as e:
            logger.error(f"Error checking zone motion: {e}")
            return {
                "zone_id": zone.get('id', 'unknown'),
                "zone_label": zone.get('label', 'unknown'),
                "motion_detected": False,
                "motion_score": 0.0,
                "error": str(e)
            }

# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "motion_engine",
        "active_detectors": len(motion_detectors)
    }

@app.get("/status")
async def get_status():
    """Get motion engine status."""
    with detectors_lock:
        detectors_info = []
        for cam_id, detector in motion_detectors.items():
            detectors_info.append({
                "camera_id": cam_id,
                "motion_detected": detector.motion_detected,
                "motion_score": detector.motion_score,
                "last_motion_time": detector.last_motion_time,
                "frame_count": detector.frame_count,
                "zones_count": len(detector.zones)
            })
    
    return {
        "active_detectors": len(motion_detectors),
        "detectors": detectors_info,
        "threshold": MOTION_THRESHOLD
    }

@app.post("/camera/{camera_id}/init")
async def init_camera(camera_id: int, threshold: float = MOTION_THRESHOLD, _: bool = Depends(verify_api_key)):
    """Initialize motion detector for a camera."""
    with detectors_lock:
        if camera_id in motion_detectors:
            del motion_detectors[camera_id]
        
        detector = MotionDetector(camera_id, threshold)
        motion_detectors[camera_id] = detector
    
    logger.info(f"Motion detector initialized for camera {camera_id}")
    return {"status": "ok", "camera_id": camera_id}

@app.post("/camera/{camera_id}/zones")
async def set_camera_zones(camera_id: int, zones: List[Dict[str, Any]], _: bool = Depends(verify_api_key)):
    """Set motion detection zones for a camera."""
    with detectors_lock:
        if camera_id not in motion_detectors:
            raise HTTPException(status_code=404, detail="Detector not found for camera")
        
        motion_detectors[camera_id].set_zones(zones)
    
    return {"status": "ok", "camera_id": camera_id, "zones_count": len(zones)}

@app.post("/camera/{camera_id}/process")
async def process_frame(camera_id: int, file: UploadFile = File(...), _: bool = Depends(verify_api_key)):
    """Process a frame for motion detection."""
    with detectors_lock:
        if camera_id not in motion_detectors:
            raise HTTPException(status_code=404, detail="Detector not found for camera")
        
        detector = motion_detectors[camera_id]
    
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image data")
    
    # Process frame
    result = detector.process_frame(frame)
    
    return result

@app.delete("/camera/{camera_id}")
async def remove_camera(camera_id: int, _: bool = Depends(verify_api_key)):
    """Remove motion detector for a camera."""
    with detectors_lock:
        if camera_id in motion_detectors:
            del motion_detectors[camera_id]
            logger.info(f"Motion detector removed for camera {camera_id}")
    
    return {"status": "ok", "camera_id": camera_id}

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Motion Detection Server...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
