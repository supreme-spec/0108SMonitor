"""Compare benchmark results from multiple detector runs.
Generate side-by-side comparison table for detector selection.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def load_reports(reports_dir: str = "tests/reports") -> Dict[str, List[Dict[str, Any]]]:
    """Load all benchmark reports from directory.
    
    Returns dict mapping detector name to list of reports (one per date).
    """
    reports = {}
    reports_path = Path(reports_dir)
    
    if not reports_path.exists():
        print(f"ERROR: Reports directory not found: {reports_dir}")
        return reports
    
    # Find all JSON reports (exclude configs)
    for json_file in sorted(reports_path.glob("*.json")):
        if "config" in json_file.name:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            detector = data.get("detector", json_file.stem.split('_')[-1])
            if detector not in reports:
                reports[detector] = []
            reports[detector].append(data)
        except Exception as e:
            print(f"Warning: Could not load {json_file}: {e}")
    
    return reports


def load_configs(configs_dir: str = "tests/configs") -> List[Dict[str, Any]]:
    """Load benchmark configuration files."""
    configs = []
    configs_path = Path(configs_dir)
    
    if not configs_path.exists():
        return configs
    
    for json_file in sorted(configs_path.glob("*.json")):
        if "config" in json_file.name:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    configs.append(json.load(f))
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
    
    return configs


def compare_detectors(reports: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Compare detector performance across all runs.
    
    Returns comparison data organized by image and scenario.
    """
    comparison = {
        "detectors": list(reports.keys()),
        "images": {},
        "summary": {},
    }
    
    # Collect all unique images
    all_images = set()
    for detector, detector_reports in reports.items():
        for report in detector_reports:
            for result in report.get("results", []):
                all_images.add(result["image"])
    
    # Build comparison matrix
    for image in sorted(all_images):
        comparison["images"][image] = {}
        
        for detector, detector_reports in reports.items():
            # Find result for this image in most recent report
            best_result = None
            best_date = None
            
            for report in detector_reports:
                for result in report.get("results", []):
                    if result.get("image") == image:
                        report_date = report.get("date", "unknown")
                        if best_date is None or report_date > best_date:
                            best_date = report_date
                            best_result = result
            
            if best_result:
                comparison["images"][image][detector] = {
                    "faces_found": best_result.get("faces_found", 0),
                    "inference_time_ms": best_result.get("inference_time_ms", 0),
                    "success": best_result.get("success", False),
                }
    
    # Calculate summary statistics
    for detector in reports.keys():
        total_faces = 0
        successful_detections = 0
        total_images = 0
        total_time = 0
        
        for image, detectors_data in comparison["images"].items():
            if detector in detectors_data:
                total_images += 1
                data = detectors_data[detector]
                total_faces += data["faces_found"]
                if data["faces_found"] > 0:
                    successful_detections += 1
                total_time += data["inference_time_ms"]
        
        comparison["summary"][detector] = {
            "total_images": total_images,
            "successful_detections": successful_detections,
            "total_faces_found": total_faces,
            "avg_inference_time_ms": round(total_time / total_images, 2) if total_images > 0 else 0,
        }
    
    return comparison


def print_comparison_table(comparison: Dict[str, Any]):
    """Print formatted comparison table to console."""
    detectors = comparison["detectors"]
    images = comparison["images"]
    
    if not detectors or not images:
        print("No data to compare.")
        return
    
    print(f"\n{'='*80}")
    print("DETECTOR COMPARISON")
    print(f"{'='*80}")
    print(f"Detectors: {', '.join(detectors)}")
    print(f"Images: {len(images)}")
    print(f"{'='*80}\n")
    
    # Print table header
    print(f"{'Image':<30} | ", end="")
    for detector in detectors:
        print(f"{detector:^10} | ", end="")
    print("\n" + "-" * 80)
    
    # Print table rows
    for image, detectors_data in sorted(images.items()):
        image_name = image[:27] + "..." if len(image) > 30 else image
        print(f"{image_name:<30} | ", end="")
        
        for detector in detectors:
            data = detectors_data.get(detector, {})
            faces = data.get("faces_found", 0)
            
            if faces > 0:
                print(f"  {faces}  | ", end="")
            elif faces == 0:
                print(f"   0  | ", end="")
            else:
                print(f"  -  | ", end="")
        
        print()
    
    print(f"{'='*80}\n")
    
    # Print summary
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Detector':<15} {'Images':<10} {'Success':<10} {'Faces':<10} {'Avg Time':<10}")
    print(f"{'-'*80}")
    
    for detector, stats in comparison["summary"].items():
        print(f"{detector:<15} {stats['total_images']:<10} {stats['successful_detections']:<10} {stats['total_faces_found']:<10} {stats['avg_inference_time_ms']:<10.2f}ms")
    
    print(f"{'='*80}\n")


def save_comparison_report(comparison: Dict[str, Any], output_dir: str = "tests/reports") -> str:
    """Save comparison report to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "detectors": comparison["detectors"],
        "total_images": len(comparison["images"]),
        "images": comparison["images"],
        "summary": comparison["summary"],
    }
    
    output_path = os.path.join(output_dir, f"{datetime.now().strftime('%Y-%m-%d')}_comparison.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nComparison report saved to: {output_path}")
    return output_path


def generate_markdown_report(comparison: Dict[str, Any], output_dir: str = "tests/reports") -> str:
    """Generate markdown report for easy reading."""
    os.makedirs(output_dir, exist_ok=True)
    
    md_lines = []
    md_lines.append("# Face Detector Comparison Report")
    md_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"\n**Detectors:** {', '.join(comparison['detectors'])}")
    md_lines.append(f"\n**Total Images:** {len(comparison['images'])}")
    
    # Summary table
    md_lines.append("\n## Summary")
    md_lines.append("\n| Detector | Images | Success | Faces | Avg Time |")
    md_lines.append("|----------|--------|---------|-------|----------|")
    
    for detector, stats in comparison["summary"].items():
        md_lines.append(f"| {detector} | {stats['total_images']} | {stats['successful_detections']} | {stats['total_faces_found']} | {stats['avg_inference_time_ms']:.2f}ms |")
    
    md_lines.append("\n## Detailed Results")
    
    # Detailed results per image
    for image, detectors_data in sorted(comparison["images"].items()):
        md_lines.append(f"\n### {image}")
        md_lines.append("\n| Detector | Faces | Time (ms) | Status |")
        md_lines.append("|----------|-------|-----------|--------|")
        
        for detector in comparison["detectors"]:
            data = detectors_data.get(detector, {})
            faces = data.get("faces_found", "-")
            time_ms = data.get("inference_time_ms", "-")
            status = "✓" if data.get("success", False) else "✗"
            
            md_lines.append(f"| {detector} | {faces} | {time_ms} | {status} |")
    
    md_lines.append("")
    
    output_path = os.path.join(output_dir, f"{datetime.now().strftime('%Y-%m-%d')}_comparison.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    
    print(f"Markdown report saved to: {output_path}")
    return output_path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare benchmark results")
    parser.add_argument("--reports", "-r", default="tests/reports",
                       help="Reports directory")
    parser.add_argument("--configs", "-c", default="tests/configs",
                       help="Configs directory")
    parser.add_argument("--markdown", "-m", action="store_true",
                       help="Generate markdown report")
    
    args = parser.parse_args()
    
    # Load data
    reports = load_reports(args.reports)
    configs = load_configs(args.configs)
    
    if not reports:
        print("No benchmark reports found.")
        print("Run benchmark_detector.py first.")
        return
    
    # Compare
    comparison = compare_detectors(reports)
    
    # Print to console
    print_comparison_table(comparison)
    
    # Save reports
    save_comparison_report(comparison, args.reports)
    
    if args.markdown:
        generate_markdown_report(comparison, args.reports)
    
    # Print config info
    if configs:
        print(f"\nAvailable configurations: {len(configs)}")
        for config in configs:
            print(f"  - {config.get('date')}: {config.get('total_tests')} tests, detectors: {', '.join(config.get('detectors', []))}")
    
    return comparison


if __name__ == "__main__":
    main()
