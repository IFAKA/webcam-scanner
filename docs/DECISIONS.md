# Decisions

- Use native Android for phone scanning.
- Use Next.js for the laptop UI.
- Use FastAPI for local backend and OpenAPI-based frontend types later.
- Do not use tRPC because backend processing is Python-first.
- Do not use paid APIs, free-tier cloud services, hosted auth, cloud storage, ARCore Geospatial/VPS, or Cloud Anchors.
- Do not use fallback scan modes. Required scanner capabilities must pass or scanning is disabled.
- Keep implementation commits below 1000 changed lines when practical; split larger work by subsystem.
