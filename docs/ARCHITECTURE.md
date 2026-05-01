# Architecture

Room Boundary Scanner is a local-first system with three runtime pieces:

1. Native Android scanner captures ARCore pose, raw depth, confidence, and quality telemetry.
2. Local FastAPI backend owns sessions, pairing, uploads, diagnostics, and processing jobs.
3. Next.js desktop UI shows scan status, diagnostics, point-cloud previews, geometry review, and exports.

The scanner is intentionally not browser-based. WebXR is useful for demos, but native Android gives stronger access to ARCore Depth, tracking state, raw depth/confidence, file storage, and device diagnostics.

## Data Flow

```text
Android ARCore
  -> WebSocket telemetry
  -> FastAPI session
  -> desktop UI live status

Android capture files
  -> HTTP upload
  -> validated session package
  -> point cloud
  -> planes
  -> editable floorplan
  -> JSON / SVG / GLB
```

## Failure Rule

The app must fail clearly when required capabilities are unavailable. Error handling improves observability; it must not silently downgrade scan behavior.
