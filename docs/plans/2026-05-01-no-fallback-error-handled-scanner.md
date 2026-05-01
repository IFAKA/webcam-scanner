# No-Fallback Error-Handled Scanner Implementation Plan

**Goal:** Build a local-only room scanner that uses native Android ARCore Depth capture, a local FastAPI backend, and a Next.js laptop UI.

**Hard rule:** scanning must work with required capabilities or fail clearly. No video-only fallback, AI-only fallback, cloud fallback, or manual-only scan mode.

## Runtime Architecture

- Phone app: native Android Kotlin + ARCore Depth.
- Laptop backend: FastAPI + Pydantic + SQLite later.
- Laptop UI: Next.js + TypeScript + Tailwind-compatible styling + Three.js later.
- Processing: OpenCV/Open3D/Shapely in later slices.
- Runtime services: local LAN only; no paid APIs, no free-tier services, no hosted auth, no cloud storage.

## Required Capability Gate

The scan button stays disabled unless all checks pass:

- Camera permission granted.
- ARCore supported and installed.
- Depth API supported.
- Raw depth frame available.
- Depth confidence frame available.
- AR tracking reaches `TRACKING`.
- Phone is paired with local laptop backend.

Each failed check must produce a stable error code and a short user-safe message.

## Error Codes

```text
DEVICE_ARCORE_UNSUPPORTED
DEVICE_DEPTH_UNSUPPORTED
DEVICE_RAW_DEPTH_UNAVAILABLE
DEVICE_TRACKING_NOT_READY
PERMISSION_CAMERA_DENIED
NETWORK_PAIRING_FAILED
NETWORK_WEBSOCKET_DROPPED
UPLOAD_INCOMPLETE
SESSION_SCHEMA_INVALID
PROCESSING_POINT_CLOUD_FAILED
PROCESSING_PLANE_FIT_FAILED
GEOMETRY_POLYGON_INVALID
EXPORT_FAILED
UNKNOWN_INTERNAL_ERROR
```

## First Implementation Slice

- Initialize open-source repo metadata and docs.
- Add shared scan states and error codes.
- Add backend capability evaluation and diagnostics skeleton.
- Add desktop UI shell showing blocked/ready capability state.
- Add native Android scanner shell with ARCore Depth capability checks.
- Treat the Vercel Web Interface Guidelines as the desktop UI acceptance checklist: keyboard access, visible focus, resilient layout, designed loading/error/blocked states, redundant status cues, and no dead-end screens.
- Use the `emil-design-eng` skill for UI polish review when changing `apps/web`.
- Keep every commit under 1000 changed lines.

## Step Completion Rule

After each implementation step:

1. Run the relevant tests and type checks.
2. Validate the changed flow works locally.
3. Fix any failures before continuing.
4. Commit the tested changes.
5. Push the commit before starting the next step.

Do not stack multiple unpushed implementation steps unless explicitly requested.

## Next Slices

1. Pairing: QR code, token validation, WebSocket telemetry.
2. Android capture: real tracking readiness, raw depth acquisition, confidence acquisition.
3. Live desktop visualization: phone pose, tracking state, sparse points.
4. Upload: scan package validation and local diagnostics bundle.
5. Geometry: point cloud, plane fitting, wall extraction, editable floorplan.
6. Export: JSON, SVG, then GLB.

## Verification

- Backend capability tests must pass locally.
- Android build requires a configured Android SDK via `ANDROID_HOME` or `local.properties`.
- Web build requires `npm install` in `apps/web`.
- No generated captures, diagnostics, build outputs, or dependency folders are committed.
