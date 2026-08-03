# Tests Directory

This directory contains test images, benchmark results, and validation tools.

## Directory Structure

```
tests/
├── images/              # Test images organized by condition
│   ├── frontal/         # Frontal face images (ideal conditions)
│   ├── profile/         # Profile/side face images
│   ├── night/           # Low-light/night images
│   ├── masks/           # Faces with face masks
│   ├── glasses/         # Faces with sunglasses/glasses
│   ├── corridor/        # Corridor/indoor scenes
│   ├── entrance/        # Entrance/gateway scenes
│   └── group/           # Multiple people in frame
│
├── scenarios/           # Images organized by deployment scenario
│   ├── entrance/        # Entrance/exit points
│   ├── corridor/        # Hallways/corridors
│   ├── checkpoint/      # Security checkpoints
│   ├── parking/         # Parking lots/garages
│   └── office/          # Office environments
│
├── output/              # Annotated images with detection results
│
├── benchmark/           # Raw benchmark data
│
└── reports/             # Generated reports and analysis

../benchmark_detector.py   # Benchmark script
../benchmark_compare.py    # Detector comparison script
../docs/development_log.md # Development journal

```

## Usage

### Running Benchmark

```bash
# Test all detectors on all images in tests/images
python benchmark_detector.py

# Custom images directory
python benchmark_detector.py -i path/to/images

# Custom output directory
python benchmark_detector.py -o path/to/reports

# Help
python benchmark_detector.py --help
```

### Comparing Results

```bash
# View comparison table in console
python benchmark_compare.py

# Generate markdown report
python benchmark_compare.py --markdown

# Help
python benchmark_compare.py --help
```

### Adding Test Images

Place images in appropriate subdirectories:

- **By condition**: `tests/images/frontal/`, `tests/images/night/`, etc.
- **By scenario**: `tests/scenarios/entrance/`, `tests/scenarios/corridor/`, etc.

### Naming Convention

Use descriptive names for test images:

```
01_frontal.jpg
02_profile.jpg
03_night_low_light.jpg
04_corridor_scene.jpg
05_group_of_three.jpg
```

## Benchmarks

### Metrics Tracked

- Face detection success rate
- Number of faces detected
- Inference time (ms)
- Bounding box coordinates
- Confidence scores

### Detector Comparison

Run benchmark to compare:

- **SCRFD** - Fast, accurate, ONNX-based
- **RetinaFace** - Accurate, especially for difficult poses
- **YOLO-Face** - Very fast, suitable for real-time

### Output Reports

After running `benchmark_detector.py`, reports are saved to `tests/reports/`:

| File | Description |
|------|-------------|
| `2026-08-03_scrfd.json` | Detection results for SCRFD on each image |
| `2026-08-03_retinaface.json` | Detection results for RetinaFace on each image |
| `2026-08-03_yoloface.json` | Detection results for YOLO-Face on each image |
| `2026-08-03_benchmark_config.json` | Configuration and summary |

JSON format includes:
```json
{
  "date": "2026-08-03",
  "detector": "scrfd",
  "results": [
    {
      "image": "entrance_01.jpg",
      "faces_found": 4,
      "inference_time_ms": 18.5,
      "image_size": {"width": 1920, "height": 1080}
    }
  ],
  "summary": {
    "total_faces_found": 24,
    "successful_detections": 6,
    "avg_inference_time_ms": 18.5
  }
}
```

## Regression Testing

After changing detector configurations or models:

1. Run benchmark on all test images
2. Compare results with previous runs
3. Check for degradation in detection rate or performance

## Contributing

When adding new images:

1. Place in appropriate directory
2. Use descriptive filename
3. Run benchmark if testing new conditions
4. Update this README if new categories added
