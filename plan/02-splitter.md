# Plan 02 — Splitter
Seq: 2/5 · Prev: 01-scaffold.md · Next: 03-labeler.md
Design ref: README#splitting-separate-script-not-in-the-labeler
Status: active · last done: step 1 · next: step 2 (blocked: ffmpeg not installed on this machine — `brew install ffmpeg`)

- [x] 1. Build adbreak/splitting.py + scripts/split_recording.py: lossless `-c copy`,
         keyframe-aligned (real keyframes probed via ffprobe), ~30-min chunks, ≥30s
         overlap via per-chunk seek, recNNN_chunkNN naming, preview (length / ~size /
         real cut points) → confirmation → progress. Unit tests for the pure planning
         logic (alignment, overlap minimum, coverage, monotonicity, naming).
      done when: pytest passes on planning logic. ✓ (10 passed)
      reverse:   pure script, no state; git revert.
- [ ] 2. Live-run on a real test recording; verify preview matches actual cut points
         and chunks play back.
      done when: a test MP4 splits into valid overlapping chunks; spot-check that each
                 chunk opens at its previewed keyframe time.
      reverse:   delete output chunks; raw recording untouched.
