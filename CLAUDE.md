# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

- **`README.md` is authoritative** for system design and build order. If anything
  here or in `plan/` disagrees with it, README wins. This file points; it never
  duplicates facts.
- **`plan/README.md`** is the execution dashboard — read its table to see where work
  stands; each sub-plan's top status line says what's next.
- **`labeler/README.md`** holds the ad-definition rule + subtypes (keep open while labeling).
- Project: ad-vs-content detector on a Samsung S21 watching a TV (camera + mic,
  outside observer — pixels/audio only). Audio primary; v1 = binary audio classifier
  (TFLite); v2 (parked) = fingerprint tier + auto-enrollment.

## Commands

```bash
# Python pipeline (pipeline/)
cd pipeline && python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'
pytest                                    # all tests
pytest tests/test_splitting.py -k name    # single test
python scripts/split_recording.py <mp4> --rec-id recNNN   # needs ffmpeg on PATH

# Labeler (labeler/)
npm ci             # .npmrc enforces ignore-scripts + exact pins — keep it that way
npm run typecheck
npm run build      # bundles src/ui.ts -> dist/app.js; then open index.html
```

## Don't relitigate (locked — rationale lives in README, don't re-derive)

- Broadcast vs OTT is **one problem** for an outside observer; no metadata access, ever.
- **Audio primary, video secondary** — but both are collected from day one.
- S21 compute is **not** the constraint; data quality is. No early HW-acceleration work.
- **Split by recording, never by clip**; balance train only; val/test stay natural ratios.
- **One config (`config/pipeline.yaml`) + one `adbreak/audio.py`** shared by
  dataset-build AND inference — never a second implementation, never hard-coded knobs.
- Offline eval on held-out MP4s is the iteration loop; live runs validate only.
- Ad = **interruption + detectable signal** (not legal category). Subtypes are
  metadata, NOT a prediction target, NOT explainability.
- Labeler is browser-based (rejected: VLC driving, in-browser splitting,
  frame-perfect tools). Splitting is a separate ffmpeg script: lossless, keyframe-
  aligned, ~30-min chunks, ≥30s overlap; preview shows REAL keyframe cut points.
- Logic lives in packages (`adbreak/`, `src/labeler.ts`); CLIs/notebooks/ui are thin.
  Colab `pip install -e`'s the package — no copy-paste into notebooks.
- npm hardening is deliberate: `ignore-scripts=true`, exact pins, aged known-good
  versions, zero runtime deps. Don't "fix" it by upgrading or loosening.
- `data/` and `models/` stay out of git. CSV labels are the irreplaceable artifact —
  they go to git/Drive.
- Rejected scope (don't reintroduce silently): custom recording app, waveform view,
  keyboard-shortcut config, separate DESIGN.md, `bumper` subtype.

## How the user works

- Act as a **colleague**: correct mistakes directly, push back when something's wrong,
  don't just agree.
- **Short, conversational responses**; bullets only when length is unavoidable.
- Never expand scope without flagging it — the user actively guards against creep.
- Budget matters: free tools (Colab free tier, open source) unless spending is justified.
- When finishing a work session, update the relevant `plan/` doc (checkboxes + status
  line + dashboard row) so the next session resumes from one line.
