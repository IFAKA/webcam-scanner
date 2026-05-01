# Roadmap

## Phase 0: Foundation

- Repository metadata and docs.
- Shared error codes and scan states.
- Local backend session and diagnostics skeleton.
- Desktop status UI shell.
- Android capability-gate skeleton.
- Desktop UI quality baseline: Vercel Web Interface Guidelines plus `emil-design-eng` polish review for accessibility, focus, resilient layout, and clear blocked/error states.

## Phase 1: Real Device Capability Probe

- Runtime ARCore support check.
- Runtime Depth API check.
- Raw depth and confidence frame acquisition.
- Tracking readiness timeout.
- Pairing with local backend.

## Phase 2: Live Telemetry

- WebSocket telemetry from phone to laptop.
- Live pose and quality status in desktop UI.
- Sparse point sample preview.

## Phase 3: Capture And Ingest

- Local scan package upload.
- Schema validation.
- Diagnostic bundle.

## Phase 4: Geometry

- Point-cloud generation.
- Plane segmentation.
- Floorplan proposal.
- Manual review and export.
