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

## Current

- [ ] Wire the Android scanner to the local FastAPI pairing endpoint.
- [ ] Display real backend-created session and pairing information in the
      desktop UI.

## Next

- [ ] Add local network configuration for phone-to-laptop API discovery.
- [ ] Submit Android capability reports to the backend after successful pairing.
- [ ] Keep scan capture blocked until all required capabilities pass.

## Verification

- Backend tests: `.venv/bin/python -m pytest services/api/tests`
- Web typecheck: `npm run typecheck` in `apps/web`
- Android build: blocked until `ANDROID_HOME` or `local.properties` is set.
- Commit size guard: `scripts/check-commit-size.sh`
