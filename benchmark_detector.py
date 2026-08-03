"""Benchmark script for face detectors.
Tests multiple detectors on images and generates comparison reports.
"""
import os
import sys
import cv2
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from ai.detectors import SCRFD, RetinaFace, YOLOFace
from ai.manager import AIManager


class BenchmarkDetector:
    """Run benchmarks on face detectors."""
    
    def __init__(self, models_dir: str = "backend/ai/models/models"):
        self.models_dir = Path(models_dir)
        self.results: List[Dict[str, Any]] = []
        
        # Initialize AIManager
        self.manager = AIManager(models_dir=str(self.models_dir))
        
        # Load detectors
        self.detectors = {
            "SCRFD": SCRFD,
            "RetinaFace": RetinaFace,
            "YOLO-Face": YOLOFace,
        }
    
    def test_image(self, image_path: Path, detector_name: str) -> Dict[str, Any]:
        """Test single image with single detector."""
        print(f"Testing: {image_path.name} with {detector_name}...")
        
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"  ERROR: Could not load image")
            return {
                "image": image_path.name,
                "detector": detector_name,
                "success": False,
                "error": "Could not load image",
            }
        
        image_size = img.shape[1], img.shape[0]  # (width, height)
        
        # Initialize detector
        detector = self.detectors[detector_name]()
        success = detector.initialize()
        if not success:
            print(f"  ERROR: Could not initialize detector")
            return {
                "image": image_path.name,
                "detector": detector_name,
                "success": False,
                "error": "Detector initialization failed",
            }
        
        # Run detection
        start_time = time.time()
        faces = detector.detect(img)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Results
        result = {
            "image": image_path.name,
            "detector": detector_name,
            "success": True,
            "image_size": {"width": image_size[0], "height": image_size[1]},
            "faces_found": len(faces),
            "inference_time_ms": round(elapsed_ms, 2),
            "faces": [],
        }
        
        # Save face details
        for i, face in enumerate(faces):
            face_data = {
                "bbox": [float(x) for x in face.bbox],
                "det_score": float(face.det_score) if hasattr(face, 'det_score') else None,
            }
            if hasattr(face, 'kps'):
                face_data["kps"] = [[float(x), float(y)] for x, y in face.kps]
            result["faces"].append(face_data)
        
        print(f"  Found {len(faces)} face(s) in {elapsed_ms:.2f}ms")
        
        return result
    
    def test_all_combinations(self, images_dir: Path) -> List[Dict[str, Any]]:
        """Test all detectors on all images in directory."""
        self.results = []
        
        # Get all images
        image_extensions = {'.jpg', '.jpeg', '.png'}
        images = [f for f in images_dir.iterdir() 
                  if f.suffix.lower() in image_extensions and f.is_file()]
        
        print(f"\n{'='*60}")
        print(f"BENCHMARK START")
        print(f"{'='*60}")
        print(f"Images: {len(images)}")
        print(f"Detectors: {', '.join(self.detectors.keys())}")
        print(f"{'='*60}\n")
        
        # Test all combinations
        for image_path in sorted(images):
            for detector_name in self.detectors.keys():
                result = self.test_image(image_path, detector_name)
                self.results.append(result)
                
                # Save annotated image if faces found
                if result["success"] and result["faces_found"] > 0:
                    self._save_annotated_result(image_path, result)
        
        return self.results
    
    def _save_annotated_result(self, image_path: Path, result: Dict[str, Any]) -> Path:
        """Save image with bounding boxes drawn."""
        img = cv2.imread(str(image_path))
        
        for face in result["faces"]:
            bbox = face["bbox"]
            x1, y1, x2, y2 = [int(x) for x in bbox]
            
            # Draw rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{result['detector']}: {face.get('det_score', 'N/A'):.2f}"
            cv2.putText(img, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save
        output_path = Path("tests/output") / f"{image_path.stem}_{result['detector']}.jpg"
        cv2.imwrite(str(output_path), img)
        
        return output_path
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate benchmark report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "detectors": list(self.detectors.keys()),
            "images_tested": len(set(r["image"] for r in self.results)),
            "total_tests": len(self.results),
            "results": self.results,
            "summary": {},
        }
        
        # Calculate summary statistics
        for detector in self.detectors.keys():
            detector_results = [r for r in self.results if r["detector"] == detector]
            
            report["summary"][detector] = {
                "total_images": len(detector_results),
                "successful_detections": sum(1 for r in detector_results if r.get("faces_found", 0) > 0),
                "total_faces_found": sum(r.get("faces_found", 0) for r in detector_results),
                "avg_inference_time_ms": sum(r.get("inference_time_ms", 0) for r in detector_results) / len(detector_results),
            }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "tests/reports") -> List[str]:
        """Save individual reports per detector per date.
        
        Returns list of saved report paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Create configs directory if not exists
        configs_dir = Path("tests/configs")
        configs_dir.mkdir(exist_ok=True)
        
        saved_paths = []
        
        # Group results by detector
        detector_results = {}
        for result in report["results"]:
            detector = result["detector"]
            if detector not in detector_results:
                detector_results[detector] = []
            detector_results[detector].append(result)
        
        # Save individual report per detector
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        for detector, results in detector_results.items():
            # Build detector report
            detector_report = {
                "date": date_str,
                "detector": detector,
                "timestamp": datetime.now().isoformat(),
                "images_tested": len(results),
                "results": results,
                "summary": {
                    "total_faces_found": sum(r.get("faces_found", 0) for r in results),
                    "successful_detections": sum(1 for r in results if r.get("faces_found", 0) > 0),
                    "avg_inference_time_ms": sum(r.get("inference_time_ms", 0) for r in results) / len(results) if results else 0,
                }
            }
            
            # Save report
            report_filename = f"{date_str}_{detector.lower()}.json"
            report_path = os.path.join(output_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(detector_report, f, indent=2, ensure_ascii=False)
            
            saved_paths.append(report_path)
            print(f"  Report saved: {report_path}")
        
        # Save configs for current run
        config_filename = f"{date_str}_benchmark_config.json"
        config_path = os.path.join(str(configs_dir), config_filename)
        
        config_data = {
            "date": date_str,
            "detectors": list(self.detectors.keys()),
            "images_directory": str(Path("tests/images").absolute()),
            "models_directory": str(self.models_dir.absolute()),
            "total_images_tested": report["images_tested"],
            "total_tests": report["total_tests"],
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        saved_paths.append(config_path)
        print(f"  Config saved: {config_path}")
        
        return saved_paths


def print_summary(report: Dict[str, Any]):
    """Print formatted summary to console."""
    print(f"\n{'='*70}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Images tested: {report['images_tested']}")
    print(f"Total tests: {report['total_tests']}")
    print(f"\n{'-'*70}")
    
    print(f"{'Detector':<15} {'Success':<12} {'Faces':<12} {'Avg Time':<12}")
    print(f"{'-'*70}")
    
    for detector, stats in report['summary'].items():
        print(f"{detector:<15} {stats['successful_detections']:<12} {stats['total_faces_found']:<12} {stats['avg_inference_time_ms']:<12.2f}ms")
    
    print(f"{'='*70}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark face detectors")
    parser.add_argument("--images", "-i", default="tests/images", 
                       help="Directory with test images")
    parser.add_argument("--output", "-o", default="tests/reports",
                       help="Output reports directory")
    parser.add_argument("--models", "-m", default="backend/ai/models/models",
                       help="Models directory")
    
    args = parser.parse_args()
    
    images_dir = Path(args.images)
    if not images_dir.exists():
        print(f"ERROR: Images directory not found: {images_dir}")
        sys.exit(1)
    
    # Initialize benchmark
    benchmark = BenchmarkDetector(models_dir=args.models)
    
    # Run tests
    results = benchmark.test_all_combinations(images_dir)
    
    # Generate and save report
    report = benchmark.generate_report()
    saved_paths = benchmark.save_report(report, args.output)
    
    # Print summary
    print_summary(report)
    
    print(f"\nTotal files saved: {len(saved_paths)}")
    for path in saved_paths:
        print(f"  - {path}")
    
    return report


if __name__ == "__main__":
    main()
