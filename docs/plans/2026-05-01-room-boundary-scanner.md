# Room Boundary Scanner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an open-source Android + laptop app that scans a room with a Redmi Note 14 5G, guides the user during capture, and produces a corrected 2D floor plan plus a simple 3D room shell.

**Architecture:** Use the phone for live ARCore/camera/depth capture and capture-quality feedback. Use the laptop for project management, review, geometry correction, heavier reconstruction, export, and persistent storage. Keep automation probabilistic and inspectable: every generated wall/measurement must expose confidence, source observations, and user-correction history.

**Tech Stack:** Android Kotlin + CameraX + ARCore Depth; local FastAPI backend; React + TypeScript + Vite desktop web UI; Three.js for 3D shell preview; OpenCV/Open3D/Shapely for geometry; SQLite + project folders for local storage.

---

## Product Decision

Build **Room Boundary Scanner**, not a generic object scanner.

The useful output is:

- A measurable 2D floor plan.
- A simplified 3D shell made of walls, floor, ceiling, doors, and openings.
- Human-correctable geometry.
- Exports: JSON first, SVG second, GLB third, DXF later.

Object scanning is intentionally deferred because photogrammetry apps already cover it well, while room-boundary capture plus correction is a sharper open-source product.

## Existing Work To Reuse Or Learn From

Use these as references, not blind copies:

- **ARCore Depth / Raw Depth:** primary Android depth source if available on-device.
- **CameraX:** camera access and recording on Android.
- **OpenCV:** calibration, reprojection error, line detection, image preprocessing.
- **Open3D:** point-cloud filtering, plane segmentation, mesh/geometry utilities.
- **Shapely:** 2D polygon validity, snapping, intersections, simplification.
- **Three.js:** browser-based 3D room-shell viewer.
- **RTAB-Map:** reference for RGB-D/stereo/lidar graph SLAM and loop closure, but too heavy for the first MVP.
- **ORB-SLAM3:** reference for visual-inertial SLAM, but GPLv3 license and integration complexity make it unsuitable as the first dependency.
- **RoomFormer / Floor-SP / FloorNet / Sigma-FP:** research references for floorplan extraction from scans; not MVP dependencies.
- **EasyFloorMap / OpenStreetMap indoor tooling:** reference for indoor maps and floorplan data concepts, not scanning geometry.

## UX Split

### Phone UI

The phone is the capture instrument.

It shows:

- Live camera feed.
- AR tracking status.
- Depth availability and depth confidence.
- Coverage map: walls/floor regions seen enough times.
- Motion feedback: too fast, too blurry, too dark, too close, too featureless.
- Required next action: start corner, pan wall, step sideways, capture doorway, close loop.
- A final checklist before upload.

The phone should not be the main editing surface.

### Computer UI

The computer is the control, review, and correction station.

It shows:

- Connected phone/session status.
- Live low-bandwidth preview from the phone.
- Capture progress timeline.
- Processing queue and logs.
- Detected floor outline.
- Wall/corner editor with snap constraints.
- Measurement scale input.
- 3D room-shell preview.
- Export panel.

### Real-Time Connection

Both devices must be on the same Wi-Fi network for MVP.

- Laptop runs local FastAPI server and WebSocket endpoint.
- Computer UI displays a QR code containing `ws://<laptop-ip>:<port>/session/<id>` plus a short pairing token.
- Android app scans the QR code and opens a WebSocket control channel.
- Phone sends live telemetry at low bandwidth: pose, tracking status, coverage stats, quality warnings, thumbnails.
- Phone stores high-volume capture data locally during scan, then uploads frames/depth/metadata after capture or in chunks.

This avoids trying to stream all camera/depth data in real time.

## Guided Capture: Confidence Model

The user should trust the scan because the app displays measurable capture criteria, not vague progress.

### Frame Quality

For each frame:

- Blur score: variance of Laplacian.
- Exposure score: percent of pixels near black/white clipping.
- Feature score: number and spatial distribution of trackable features.
- Depth score: fraction of pixels with valid depth and confidence above threshold.
- Pose score: ARCore tracking state and pose covariance proxy where available.

A frame is useful only if it passes minimum thresholds.

### Coverage Quality

Represent the room as a provisional 2D angular/planar coverage map around the scan path.

For each candidate wall segment, require:

- At least `N` accepted observations.
- Observations from at least two viewing angles separated by `theta_min`.
- Median depth confidence above `c_min`.
- Reprojection residual below `epsilon_px`.
- Plane residual below `epsilon_m`.

### User-Facing Capture States

The app maps metrics into simple states:

- `Need more wall coverage`
- `Move slower`
- `Too dark`
- `Wall has low texture; move closer or include corners`
- `Doorway captured`
- `Loop closure recommended`
- `Ready to process`

The app never shows "done" unless coverage and uncertainty thresholds pass.

## Math Validation

### Calibration / Reprojection

For a detected 3D point `X_i` and observed image point `x_i`, projection is:

```text
x_hat_i = K [R | t] X_i
e_i = ||x_i - x_hat_i||_2
RMS = sqrt((1 / n) * sum(e_i^2))
```

OpenCV uses reprojection error as the core calibration/pose quality metric. Lower RMS means the estimated camera model better explains observed points.

Acceptance rule:

```text
RMS <= 2 px: usable
RMS <= 1 px: good
RMS > 3 px: warn / reject for geometry extraction
```

### Scale Anchor

Monocular visual reconstruction has scale ambiguity:

```text
project(K, R, t, X) = project(K, R, s*t, s*X)
```

for any positive scale `s`, the image projection is unchanged. Therefore if ARCore metric scale is unavailable or unstable, the user must enter one known real-world length.

If the user marks two floorplan points with current estimated length `L_est` and real length `L_real`:

```text
s = L_real / L_est
X_corrected = s * X_est
```

### Depth Uncertainty

For stereo/triangulation-style depth intuition:

```text
Z = f * B / d
dZ/dd = -f * B / d^2
sigma_Z ~= (Z^2 / (f * B)) * sigma_d
```

Depth error grows quadratically with distance. This proves why the guided capture must ask the user to move closer to distant/low-confidence walls instead of accepting long-range guesses.

### Plane Fitting

For wall/floor plane:

```text
plane: n dot x + b = 0
r_i = |n dot x_i + b|
RMSE_plane = sqrt((1 / n) * sum(r_i^2))
```

Acceptance rule:

```text
RMSE_plane <= 0.05 m: good wall/floor plane
0.05 m < RMSE_plane <= 0.12 m: usable but warn
> 0.12 m: reject or require user correction
```

### Floorplan Polygon Validity

The final 2D floorplan must satisfy:

- Polygon is closed.
- No self-intersections.
- Area is positive.
- Adjacent wall angles are snapped only when within an angle tolerance, e.g. `abs(theta - 90deg) <= 7deg`.
- User edits override automatic geometry and are stored as authoritative.

## Agentic Architecture

Keep agents/modules small and context-limited.

- `capability-agent`: detects ARCore, Depth API, camera, gyro, and network availability.
- `capture-agent`: owns Android scan session and quality metrics.
- `sync-agent`: owns pairing, WebSocket telemetry, upload, resumability.
- `ingest-agent`: validates uploaded session files and writes normalized metadata.
- `reconstruction-agent`: creates sparse/depth point observations and camera tracks.
- `geometry-agent`: extracts floor/wall planes and converts them into 2D polygons.
- `editor-agent`: owns correction UX, snapping, validation, undo/redo.
- `export-agent`: writes JSON/SVG/GLB/DXF.
- `qa-agent`: owns fixtures, golden exports, scan-quality regression tests.

Shared context files only:

- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/DECISIONS.md`
- `docs/ROADMAP.md`
- `docs/plans/*`

Rule: an agent may read only its module, tests for that module, and the shared context files unless a task explicitly requires more.

## Open-Source Workflow

Repository must be initialized before implementation.

Commit policy:

- Each commit should be below 1000 changed lines.
- If a task exceeds 1000 changed lines, split by module, not by arbitrary file count.
- Every commit should compile or include a clear `WIP docs-only` label.
- Prefer TDD for geometry, contracts, exports, and quality scoring.
- Large generated files, scan fixtures, and binary captures must not be committed unless intentionally added as small test fixtures.

License recommendation:

- App code: Apache-2.0 or MIT.
- Avoid GPL dependencies in core code unless the whole project accepts GPL obligations.
- ORB-SLAM3 should remain a reference or optional external adapter, not a linked core dependency.

## Implementation Phases

### Phase 0: Repository Foundation

- Initialize git.
- Add license, README, contributing guide, code of conduct.
- Add architecture docs and data contracts.
- Add commit-size check script.

### Phase 1: Capability Probe

- Android app detects ARCore availability.
- Android app detects Depth API support at runtime.
- Android app reports camera formats, gyro, accelerometer, and network status.
- Desktop UI displays one result: best available capture mode.

### Phase 2: Pairing And Live Telemetry

- Laptop starts FastAPI server.
- Desktop UI shows QR pairing code.
- Phone connects over WebSocket.
- Phone sends pose/tracking/depth/quality telemetry.
- Desktop shows live status and warnings.

### Phase 3: Guided Capture MVP

- Phone records AR/depth/camera session metadata.
- Phone computes blur/exposure/depth/coverage scores.
- Phone displays actionable capture instructions.
- Session can be uploaded to laptop.

### Phase 4: Manual Floorplan Editor

- Desktop lets user draw walls over a reference frame.
- User enters one known measurement.
- Editor validates polygon closure and intersections.
- Export JSON and SVG.

### Phase 5: Assisted Geometry

- Backend extracts depth points and candidate planes.
- Geometry agent proposes walls/floor outline.
- Editor shows confidence per wall.
- User accepts/corrects suggestions.

### Phase 6: 3D Shell Export

- Generate simple room shell from corrected floorplan.
- Preview with Three.js.
- Export GLB.

### Phase 7: Test Scan Protocol

- Define repeatable scan exercises.
- Track accuracy against tape-measured rooms.
- Add regression fixtures and golden outputs.

## First Build Slice

The first real implementation should be deliberately small:

1. Git repo + docs.
2. Android capability probe.
3. Desktop pairing page.
4. WebSocket telemetry from phone to desktop.
5. No reconstruction yet.

This proves the hardware and real-time UX before building geometry.

