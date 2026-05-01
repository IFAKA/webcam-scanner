# Room Boundary Scanner

Local-only room scanning with a native Android ARCore scanner, a laptop web control room, and local Python processing.

## Hard Requirement

Scanning is available only when every required capability passes:

- ARCore is supported and installed.
- ARCore Depth API is supported.
- Raw depth and confidence frames are available.
- AR tracking reaches `TRACKING`.
- Camera permission is granted.
- The phone is paired with the laptop over the local network.

If any requirement fails, the app must refuse to scan and show a stable error code. There is no video-only, AI-only, cloud, or manual fallback scan mode.

## Local-Only Policy

The project does not require paid APIs, free-tier cloud services, hosted auth, cloud storage, hosted telemetry, ARCore Geospatial/VPS, or Cloud Anchors. Internet access is only needed to install dependencies.

## Workspace

- `apps/android-scanner`: native Android scanner.
- `apps/web`: Next.js desktop control room.
- `services/api`: local FastAPI backend.
- `shared/contracts`: shared schemas and error codes.
- `docs`: architecture and implementation notes.

## First Slice

This repository currently implements the foundation for capability gating, error contracts, local backend diagnostics, and a desktop scan status shell. Reconstruction and exports are built in later slices.
