Concise rules for building accessible, fast, polished UIs in this repository.

## Product Fit

- Build the actual local room-scanning control room, not a marketing page.
- Treat the laptop UI as an operational tool: dense, scannable, predictable, and resilient under error states.
- Keep the no-fallback rule visible in UX decisions: blocked states must explain the next action, never imply scanning can continue without required capabilities.

## Vercel Web Interface Guidelines

Use https://vercel.com/design/guidelines as the UI review checklist for `apps/web`.

- MUST support keyboard operation for every flow.
- MUST show visible `:focus-visible` states and keep focus management explicit.
- MUST use native semantics first: `button` for actions, `a`/`Link` for navigation, labels for controls.
- MUST provide a skip link and hierarchical headings.
- MUST make hit targets at least 24 px, and 44 px on mobile.
- MUST keep browser zoom enabled.
- MUST set mobile inputs to at least 16 px when inputs are introduced.
- MUST include all meaningful states: empty, loading, sparse, dense, blocked, success, and error.
- MUST use redundant status cues; never rely on color alone.
- MUST handle long identifiers, tokens, URLs, diagnostics, and generated content without breaking layout.
- MUST keep stateful UI deep-linkable when filters, tabs, pagination, expanded panels, or editor modes are added.
- MUST announce async updates and validation with polite live regions when dynamic flows are added.
- MUST confirm destructive actions or provide an undo window.
- MUST honor `prefers-reduced-motion`; prefer CSS animations using `transform` and `opacity`.
- NEVER use `transition: all`.
- SHOULD use `Intl.*` for dates, times, numbers, and units.
- SHOULD wrap product names, code tokens, session ids, and technical identifiers with `translate="no"` when useful.

## Design Engineering Skill

Use the installed `emil-design-eng` skill as a polish review lens for UI work.

- Buttons and pressable controls should feel responsive with clear hover, active, and focus states.
- Animations need a purpose: feedback, spatial continuity, state indication, or deliberate rare delight.
- Frequent operational interactions should stay instant or nearly instant.
- If animation is added, use explicit properties, short durations, and strong easing.
- Prefer precise alignment, consistent radii, crisp borders, and useful contrast over decorative effects.

## Verification

Before finishing meaningful `apps/web` UI changes:

- Run `npm run typecheck` in `apps/web` when dependencies are installed.
- Run `npm run build` when the change affects routing, metadata, or server/client behavior.
- Inspect mobile, laptop, and wide layouts; verify text and diagnostics do not overflow incoherently.
