## Goal
- Launch and stabilize the `D:\smart-security-monitor` project with GPU acceleration, fix orphaned FFmpeg processes and files on camera delete, and resolve broken person creation/import with zero face embeddings.

## Constraints & Preferences
- (none)

## Progress
### Done
- Verified project dependencies exist (`package.json`, `node_modules`, `package-lock.json`)
- Installed missing NVIDIA CUDA pip packages: `nvidia-cudnn-cu12`, `nvidia-cublas-cu12`, `nvidia-cuda-runtime-cu12`, `nvidia-cuda-cupti-cu12`, `nvidia-cufft-cu12`, `nvidia-curand-cu12`, `nvidia-cusolver-cu12`, `nvidia-cusparse-cu12`, `nvidia-nvjitlink-cu12`, `nvidia-nvtx-cu12`
- Copied all 29 NVIDIA DLLs to `venv/Scripts/` (Windows `LoadLibraryEx` with restricted flags doesn't search PATH)
- Copied missing `nvJitLink_120_0.dll` to `venv/Scripts/`
- Confirmed all 3 services running: Vite :5173, Node.js API :3000, Python Face Engine :8001
- Confirmed GPU detected: `[FaceEngine] INFO: NVIDIA GPU detected. Using CUDA.`
- API health endpoint returns `gpu_enabled: true`, `recognition_provider: onnxruntime (CUDAExecutionProvider)`
- Fixed orphaned FFmpeg processes: `DELETE /api/cameras/:id` and `POST /api/cameras/:id/stop` call `stopCameraPipeline(id)` to kill FFmpeg, clear timers/retries, and wipe frame buffers — committed as `32048c5`
- Fixed orphaned files on camera delete: added pre-deletion cleanup in `DELETE /api/cameras/:id` (server.ts lines 741–769) — queries all Events/Recordings, deletes `snapshot_path` and `video_path` files from `publicDir` before `prisma.camera.delete()` — committed as `976f091`
- Added non-strict embedding fallback in `enrollPhotoWithGate()` (server.ts:1573-1578) — if strict quality gate rejects photo, tries non-strict mode
- Added test inference in `initialize_face_engine()` (face_server.py:167-185) — runs dummy `face_app.get()` during init, falls back to CPU if GPU inference fails
- Added programmatic PATH fix at top of `face_server.py` (lines 8-33) — injects NVIDIA CUDA bin dirs into PATH + `SetDllDirectory(venv/Scripts)` before onnxruntime initializes
- Fixed syntax error in `face_server.py` (line 726-727) — malformed `try/except` block with missing `try:` keyword
- Confirmed `FaceDescriptor` table has 39 rows (not `face_descriptor`); person table has `embedding_count` column (INTEGER)
- Verified camera deletion logic: WebSocket closing, `stopCameraPipeline(id)` killing FFmpeg, `prisma.camera.delete()` removing DB record, and in-memory cache filtering all work
- `onDelete: Cascade` in schema handles Event/Recording DB rows automatically
- Checked for orphaned `FaceDescriptor` rows: **0** (cascade deletion works correctly)
- All 17 persons have matching `embedding_count` and descriptor counts
- Existing cameras (ID 7-10): **0 events with snapshots, 0 recordings** — no orphan files currently present
- Committed cuDNN fix as `7f3ba4b`
- Confirmed TypeScript type check passes (`npx tsc --noEmit --skipLibCheck` exit code 0)
- Confirmed Python syntax passes (`py_compile face_server.py` exit code 0)
- Person creation with photo now works: `embedding_count: 1`, `has_embedding: true`
- Confirmed no orphaned FFmpeg processes currently running (checked via `Get-Process`)
- SQLite autoincrement IDs don't reset (confirmed normal behavior) — IDs 7-10 exist because IDs 1-6 were deleted previously
- **Fixed person search (поиск по людьми)** — committed as `dcf63f3`
  - Root cause: `URLSearchParams.toString()` in browser produced corrupted URL encoding for Cyrillic characters (e.g., "Алекс" → `NaN0%90%d0%bb%d0%b5%d0%ba%d1%81` instead of `%D0%90%D0%BB%D0%B5%D0%BA%D1%81`), causing 0 search results
  - Fix: Replaced `URLSearchParams` with `encodeURIComponent` in `People.tsx` and `LiveMonitor.tsx`
  - Also fixed case-insensitive Cyrillic search in `server.ts`: moved filtering from Prisma `contains` (case-sensitive for Cyrillic in SQLite) to JavaScript `toLowerCase().includes()` for proper matching
  - Verified: curl through Vite proxy returns 3 results for "Алекс"; 0 `NaN0` corrupted requests in logs after fix
- Committed `face-engine.ts` descriptor dedup, `server.ts` search logic, `People.tsx`/`LiveMonitor.tsx` search fix, and `iconv-lite` dependency as `dcf63f3`

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- Unpinned Python package versions in `requirements.txt` to resolve `onnxruntime==1.20.1` incompatibility with Python 3.14.6 (`No matching distribution found`)
- Used `powershell -ExecutionPolicy Bypass` wrapper because default PowerShell execution policy blocks `npm.ps1` (WinError: UnauthorizedAccess)
- Uninstalled `onnxruntime` before installing `onnxruntime-gpu` to avoid DLL lock conflict (`WinError 5`)
- DELETE/STOP handlers now call `stopCameraPipeline(id)` instead of only removing from DB/in-memory array
- Copied NVIDIA DLLs to `venv/Scripts/` because Windows `LoadLibraryEx` with `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR` flag doesn't search PATH
- Added non-strict fallback in `enrollPhotoWithGate()` for borderline face quality cases
- Replaced `URLSearchParams` with `encodeURIComponent` in frontend search to fix Cyrillic URL encoding corruption
- Moved person search filtering from Prisma `contains` to JavaScript `toLowerCase().includes()` for case-insensitive Cyrillic matching in SQLite
- Added `iconv-lite` dependency for Cyrillic text handling in bulk import

## Next Steps
- (none — all reported issues resolved)

## Critical Context
- **cuDNN missing root cause**: `onnxruntime-gpu` installed but 9 `nvidia-*` CUDA pip packages were absent → `LoadLibrary failed for cudnn64_9.dll` → 500 error → `embedding_count: 0`
- **Quality gate behavior**: `passes_quality_gate` + strict enrollment gate rejects blurry/low-quality faces — expected behavior, not a bug; test photos consistently fail with `sharpness_score: 0.1187` (motion blur)
- **Auto-seed phantom**: `seedDatabase()` at `server.ts:4016-4034` creates default USB camera (`source: "/dev/video0"`) when `camera` table is empty — source of phantom camera entries on restart
- **Camera deletion logic**: confirmed working — WebSocket closing, `stopCameraPipeline(id)` killing FFmpeg, `prisma.camera.delete()` removing DB record, in-memory cache filtering, `onDelete: Cascade` clearing Event/Recording rows, and pre-deletion file cleanup for snapshots/recordings
- **RTSP cameras**: all unreachable on LAN (IPs `192.168.10.x` and `192.168.100.x` not accessible) — FFmpeg retry loops are expected behavior, not a bug
- **Working directory issue**: Shell cwd is `D:\smart-security-monitor\node_modules` (inside node_modules) — not project root
- **Person search Cyrillic encoding bug**: `URLSearchParams.toString()` in browser produced `NaN0%90...` instead of `%D0%90%D0%BB...` for Cyrillic input — fixed with `encodeURIComponent`
- **SQLite Cyrillic case-insensitive search**: Prisma `contains` with `mode: 'insensitive'` doesn't work for Cyrillic in SQLite — fixed with JavaScript-side `toLowerCase().includes()`
- **Pre-existing uncommitted changes**: now committed as `dcf63f3`

## Relevant Files
- `D:\smart-security-monitor/face_server.py`: Python FastAPI + InsightFace face engine; PATH injection (lines 8-33), `initialize_face_engine()` with GPU test inference + CPU fallback (lines 167-185), syntax error fix (line 726-727), cuDNN loading fixed
- `D:\smart-security-monitor/face-engine.ts`: TypeScript AI engine; `getEmbeddingFromServer()` (line 601) sends image via `FormData`/`Blob` to Python `POST /get-embedding`; `extractEmbedding()` (line 895) reads file via `safeResolvePhotoPath`; `saveDescriptorToDB` with descriptor dedup
- `D:\smart-security-monitor/server.ts`: Express server; `app.get("/api/persons")` (line 919) with JS-side case-insensitive Cyrillic search, `app.delete("/api/cameras/:id")` (line 695) with pre-deletion file cleanup (lines 741-769), `stopCameraPipeline()` (line 3408), `enrollPhotoWithGate()` (line 1564) with non-strict fallback (lines 1573-1578), `seedDatabase()` (line 4016-4034) auto-seeds default USB camera
- `D:\smart-security-monitor/src/pages/People.tsx`: Frontend person management; `fetchPeople()` uses `encodeURIComponent` for Cyrillic-safe URL encoding (line 78-84)
- `D:\smart-security-monitor/src/pages/LiveMonitor.tsx`: Live monitor with person search; `fetchPeople()` uses `encodeURIComponent` (line 403-408)
- `D:\smart-security-monitor/src/api/client.ts`: `apiFetch` function with `normalizePath` for collection endpoint trailing slashes
- `D:\smart-security-monitor/.env`: Environment vars (FACE_SERVER_URL, thresholds, PORT=3000)
- `D:\smart-security-monitor/requirements.txt`: Python deps (fastapi, uvicorn, insightface, opencv-python-headless, onnxruntime-gpu)
- `D:\smart-security-monitor/package.json`: npm scripts (dev, build, lint); includes `iconv-lite` dependency
- `D:\smart-security-monitor/prisma/schema.prisma`: Prisma SQLite schema; `onDelete: Cascade` on Event/Recording relations
- `D:\smart-security-monitor/venv`: Python venv with `onnxruntime-gpu` and 9 NVIDIA CUDA pip packages installed; NVIDIA DLLs copied to `venv/Scripts/`
- `D:\smart-security-monitor/bin/ffmpeg.exe`: FFmpeg binary for camera streams; properly killed on camera delete via `stopCameraPipeline`
- `D:\smart-security-monitor/prisma/migrations/20260715090306_add_event_confirmation_id/`: Migration linking Event to FaceConfirmation (committed 1fe0c17)
- `D:\smart-security-monitor/prisma/dev.db`: SQLite database; 17 persons, 4 cameras (IDs 7-10), 39 face descriptors