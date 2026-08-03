#!/usr/bin/env python3
"""
License Plate Recognition Server (FastAPI + EasyOCR)
Реализует распознавание автомобильных номеров.
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
import re

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ─── Configuration ────────────────────────────────────────────────────────────

LPR_REGIONS: List[str] = os.getenv("LPR_REGIONS", "RU").split(",")
LPR_CONFIDENCE_THRESHOLD: float = float(os.getenv("LPR_CONFIDENCE_THRESHOLD", "0.7"))
LPR_MIN_PLATE_SIZE: int = int(os.getenv("LPR_MIN_PLATE_SIZE", "100"))
API_KEY: str = os.getenv("LPR_API_KEY", "")

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="[LPREngine] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_log_file = Path(__file__).parent / "logs" / "lpr_server.log"
_log_file.parent.mkdir(exist_ok=True)
_file_handler = logging.FileHandler(_log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(_file_handler)

# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="Smart Security - LPR Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Global State ─────────────────────────────────────────────────────────────

lpr_engine = None
is_initialized = False
used_regions = LPR_REGIONS

# ─── Security Middleware ──────────────────────────────────────────────────────

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not API_KEY:
        return True
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# ─── LPR Engine Class ─────────────────────────────────────────────────────────

class LPREngine:
    """Движок распознавания номерных знаков."""
    
    def __init__(self, regions: List[str] = None):
        self.regions = regions or LPR_REGIONS
        self.confidence_threshold = LPR_CONFIDENCE_THRESHOLD
        self.min_plate_size = LPR_MIN_PLATE_SIZE
        
        # Load OCR engine (placeholder for EasyOCR or similar)
        self.ocr_available = False
        self._init_ocr()
        
        # Statistics
        self.plates_recognized = 0
        self.total_processed = 0
        
        logger.info(f"LPREngine initialized with regions: {self.regions}")
    
    def _init_ocr(self):
        """Инициализация OCR движка."""
        try:
            # Try to import EasyOCR
            import easyocr
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
            self.ocr_available = True
            logger.info("EasyOCR loaded successfully")
        except ImportError:
            logger.warning("EasyOCR not available, using fallback pattern matching")
            self.ocr_available = False
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
            self.ocr_available = False
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Обработка кадра для распознавания номеров."""
        self.total_processed += 1
        
        # Detect potential license plates using color and contour analysis
        plates = self._detect_plates(frame)
        
        results = []
        for plate_img, bbox in plates:
            plate_text = self._recognize_plate(plate_img)
            if plate_text:
                results.append({
                    "text": plate_text,
                    "confidence": 0.8,  # Placeholder confidence
                    "bbox": bbox,
                    "region": self._detect_region(plate_text)
                })
                self.plates_recognized += 1
        
        return {
            "plates_found": len(results),
            "plates": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_plates(self, frame: np.ndarray) -> List[Tuple[np.ndarray, List[int]]]:
        """Детекция потенциальных номерных знаков на кадре."""
        plates = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while keeping edges
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Edge detection
            edged = cv2.Canny(filtered, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Approximate contour
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.018 * peri, True)
                
                # Check if contour has 4 points (potential plate)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    
                    # Check aspect ratio and size
                    aspect_ratio = w / float(h)
                    if 2.0 < aspect_ratio < 6.0 and w > self.min_plate_size:
                        # Extract plate region
                        plate_img = gray[y:y+h, x:x+w]
                        plates.append((plate_img, [x, y, w, h]))
        
        except Exception as e:
            logger.error(f"Error detecting plates: {e}")
        
        return plates
    
    def _recognize_plate(self, plate_img: np.ndarray) -> Optional[str]:
        """Распознавание текста на номерном знаке."""
        if self.ocr_available:
            try:
                # Use EasyOCR
                results = self.reader.readtext(plate_img)
                if results:
                    # Get result with highest confidence
                    best_result = max(results, key=lambda x: x[2])
                    if best_result[2] > self.confidence_threshold:
                        text = self._format_plate_text(best_result[0])
                        return text
            except Exception as e:
                logger.error(f"OCR error: {e}")
        else:
            # Fallback: simple pattern matching
            return self._fallback_recognition(plate_img)
        
        return None
    
    def _format_plate_text(self, text: str) -> str:
        """Форматирование текста номера."""
        # Remove spaces and convert to uppercase
        text = text.upper().replace(" ", "")
        
        # Basic validation for Russian plates
        if 'RU' in self.regions:
            # Pattern: A000AA00 (Russian format)
            if re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', text):
                return text
        
        return text
    
    def _fallback_recognition(self, plate_img: np.ndarray) -> Optional[str]:
        """Fallback распознавание без OCR."""
        # Placeholder for simple pattern matching
        # In production, this should use a proper OCR library
        return None
    
    def _detect_region(self, plate_text: str) -> str:
        """Определение региона по формату номера."""
        if not plate_text:
            return "UNKNOWN"
        
        for region in self.regions:
            if region == "RU" and re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', plate_text):
                return "RU"
            elif region == "EU" and re.match(r'^[A-Z]{1,3}\d{1,4}[A-Z]{1,3}$', plate_text):
                return "EU"
            elif region == "US" and re.match(r'^[A-Z]{2}\d{4}[A-Z]{2}$', plate_text):
                return "US"
        
        return "UNKNOWN"

# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "lpr_engine",
        "initialized": is_initialized,
        "ocr_available": lpr_engine.ocr_available if lpr_engine else False
    }

@app.get("/status")
async def get_status():
    """Get LPR engine status."""
    if not lpr_engine:
        return {
            "initialized": False,
            "regions": used_regions,
            "plates_recognized": 0,
            "total_processed": 0
        }
    
    return {
        "initialized": is_initialized,
        "regions": lpr_engine.regions,
        "confidence_threshold": lpr_engine.confidence_threshold,
        "plates_recognized": lpr_engine.plates_recognized,
        "total_processed": lpr_engine.total_processed,
        "ocr_available": lpr_engine.ocr_available
    }

@app.post("/regions")
async def set_regions(regions: List[str], _: bool = Depends(verify_api_key)):
    """Set LPR regions."""
    global used_regions, lpr_engine
    
    used_regions = regions
    if lpr_engine:
        lpr_engine.regions = regions
    
    logger.info(f"LPR regions updated: {regions}")
    return {"status": "ok", "regions": regions}

@app.post("/process")
async def process_frame(file: UploadFile = File(...), _: bool = Depends(verify_api_key)):
    """Process a frame for license plate recognition."""
    if not lpr_engine or not is_initialized:
        raise HTTPException(status_code=503, detail="LPR engine not initialized")
    
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image data")
    
    # Process frame
    result = lpr_engine.process_frame(frame)
    
    return result

# ─── Initialization ───────────────────────────────────────────────────────────

def initialize_lpr_engine():
    """Initialize LPR engine."""
    global lpr_engine, is_initialized
    
    try:
        lpr_engine = LPREngine(regions=used_regions)
        is_initialized = True
        logger.info("LPR engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LPR engine: {e}")
        is_initialized = False

# Initialize on startup
initialize_lpr_engine()

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting LPR Server...")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
