# Plan 02 — Splitter
Seq: 2/5 · Prev: 01-scaffold.md · Next: 03-labeler.md
Design ref: README#splitting-separate-script-not-in-the-labeler
Status: active · last done: step 2 (synthetic) · next: step 2 on a real phone recording

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
      progress:  ffmpeg 8.1.1 installed (2026-06-06). Machinery verified end-to-end on
                 a synthetic 65-min recording (lavfi testsrc): 3 chunks, actual
                 durations matched the preview exactly, ≥30s overlap held. Still open:
                 run on a REAL phone recording (variable framerate, real keyframe
                 spacing) once the first session is recorded.
