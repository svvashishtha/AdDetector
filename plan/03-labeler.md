# Plan 03 — Labeler
Seq: 3/5 · Prev: 02-splitter.md · Next: 04-collection.md
Design ref: labeler/README.md (tool spec + ad-definition rule)
Status: done · last done: step 2 · next: —

- [x] 1. Build the tool: index.html + src/labeler.ts (logic, no DOM) + src/ui.ts
         (wiring). Mark start/end from video.currentTime into editable fields, ±0.5s
         nudge, category dropdown (commercial default), Save Ad clears fields,
         editable segment list with delete + jump-to-verify, CSV import/export.
         Hardening: .npmrc ignore-scripts=true, exact-pinned esbuild+typescript,
         committed lockfile, zero runtime deps.
      done when: typecheck + build pass; CSV export → re-import round-trips correctly.
      reverse:   git revert; no data touched.
- [x] 2. Verify logic: round-trip test (export → parse → identical segments + source),
         nudge clamping, mm:ss parsing, validation, partial import of bad lines.
      done when: all checks pass in node against the bundled module. ✓
      reverse:   n/a (read-only checks).
