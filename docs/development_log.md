# Development Log

Journal of project development and milestones.

---

## 2026-08-03

### AI Architecture Stage — Completed

**Status:** ✅ Completed

**Summary:**
- `AIManager` implemented as Singleton with lazy loading
- `Router` implemented to switch between detectors
- `SCRFD` detector integrated with `buffalo_l` model
- `ArcFace` recognizer connected
- `FAISS` vector database prepared
- `InsightFaceLoader` singleton for model management

**Key Technical Decisions:**
- Lazy loading: models loaded on-demand only when needed
- Singleton pattern: single instance of InsightFaceLoader across the project
- Router pattern: ability to switch detectors without code changes

**Test Results:**
- `SCRFD.initialize()` successfully loads `buffalo_l` model
- ONNX Runtime uses CPU execution provider (no GPU available)
- Independent test confirms same behavior as integrated system

**Known Issues:**
- Test image `assets/test_face.jpg` does not contain detectable face (0 edges, low contrast)
- No face detected by SCRFD, Haar Cascade, or buffalo_l on test image
- Need real photos with faces to validate detector performance

**Next Steps:**
- Collect real images from target cameras
- Create benchmark suite with multiple detectors
- Test SCRFD, RetinaFace, YOLO-Face on real scenarios

---

### AI Validation Stage — Waiting

**Status:** ⏸️ Waiting

**Reason:** Missing reference image dataset.

**Required Actions:**
- Gather real photos from surveillance cameras
- Organize images by scenario: entrance, corridor, checkpoint, parking, office
- Organize images by condition: frontal, profile, night, masks, glasses
- Run benchmark tests on collected images

**Expected Deliverables:**
- Benchmark report comparing SCRFD vs RetinaFace vs YOLO-Face
- Detector recommendations per scenario (entrance, corridor, etc.)
- Performance metrics (accuracy, inference time)
- Regression test suite for future changes

---

## File Structure

```
tests/
├── images/               # Test images organized by condition
│   ├── frontal/          # Frontal face images
│   ├── profile/          # Profile face images
│   ├── night/            # Low-light images
│   ├── masks/            # Faces with masks
│   ├── glasses/          # Faces with glasses
│   ├── corridor/         # Corridor scenes
│   ├── entrance/         # Entrance scenes
│   └── group/            # Group photos
│
├── scenarios/            # Images organized by deployment scenario
│   ├── entrance/
│   ├── corridor/
│   ├── checkpoint/
│   ├── parking/
│   └── office/
│
├── output/               # Benchmark results with annotated images
│
├── benchmark/            # Raw benchmark data
│
└── reports/              # Generated reports

docs/
└── development_log.md    # This file
```

---

## Notes

- All technical decisions are documented as they are made
- Known issues are tracked and will be revisited when new data becomes available
- Stage transitions are recorded with clear reasoning
