# Development Status

This file is the source-of-truth checklist for active development. Update it
with every code change.

## Completed

- [x] Repository foundation and local-only project docs.
- [x] Stable scan states and scanner error codes.
- [x] FastAPI session creation, diagnostics, and capability evaluation.
- [x] Next.js desktop scan status shell.
- [x] Native Android scanner capability shell.
- [x] Android capability validation for camera permission, ARCore install/support,
      motion sensors, Raw Depth support, local pairing flag, and observed Redmi
      Note 14 5G identity display.
- [x] Server-owned local pairing token validation.
- [x] Capability submission uses backend pairing state instead of trusting the
      phone-reported network flag.
- [x] Android scanner can pair with the local FastAPI endpoint using a
      desktop-provided API URL, session ID, and pairing token.
- [x] Desktop UI creates a backend session and displays pairing values for the
      Android scanner.
- [x] Add local network configuration for phone-to-laptop API discovery.
- [x] Submit Android capability reports to the backend after successful pairing.
- [x] Desktop UI polls the backend session and surfaces the submitted capability
      report.
- [x] Keep scan capture blocked until all required capabilities pass.
- [x] Start the scan capture flow only from a backend READY session.

## Current

- [ ] Stream live scan telemetry from Android to the backend.

## Next

- [ ] Persist captured scan frames and required metadata for upload.
- [ ] Process uploaded scan data into reviewable room geometry.
- [ ] Add desktop review controls for boundaries, dimensions, and export.

## Verification

- Backend tests: `.venv/bin/python -m pytest services/api/tests`
- Web typecheck: `npm run typecheck` in `apps/web`
- Android build: blocked until `ANDROID_HOME` or `local.properties` is set.
- Commit size guard: `scripts/check-commit-size.sh`
