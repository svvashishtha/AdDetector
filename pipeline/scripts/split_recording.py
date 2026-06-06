#!/usr/bin/env python3
"""Split a raw recording into lossless, keyframe-aligned, overlapping chunks.

Thin CLI — all logic lives in adbreak.splitting. Previews the REAL keyframe cut
points (lossless cuts can't land on idealized marks), waits for confirmation,
then splits with progress.

Usage:
    python scripts/split_recording.py /path/to/recording.mp4 --rec-id rec001
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adbreak.config import load_config
from adbreak.splitting import (
    format_timestamp,
    plan_chunks,
    probe_duration,
    probe_keyframes,
    split_recording,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="raw recording (MP4)")
    parser.add_argument("--rec-id", required=True,
                        help="recording id for provenance, e.g. rec001")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="output dir (default: data/chunks/<rec-id>)")
    parser.add_argument("--yes", action="store_true",
                        help="skip the confirmation prompt")
    args = parser.parse_args()

    cfg = load_config().splitting
    out_dir = args.out_dir or Path(__file__).resolve().parents[2] / "data" / "chunks" / args.rec_id

    print(f"Probing {args.input.name} …")
    duration = probe_duration(args.input)
    keyframes = probe_keyframes(args.input)
    plans = plan_chunks(duration, keyframes, cfg.chunk_seconds, cfg.overlap_seconds,
                        args.rec_id, total_bytes=args.input.stat().st_size)

    print(f"\nRecording: {format_timestamp(duration)} "
          f"({args.input.stat().st_size / 1e9:.2f} GB), {len(keyframes)} keyframes")
    print(f"Plan: {len(plans)} chunks of ~{cfg.chunk_minutes:g} min, "
          f"≥{cfg.overlap_seconds:g}s overlap, cuts on real keyframes → {out_dir}\n")
    print(f"  {'chunk':<16} {'start (keyframe)':>17} {'end':>10} {'length':>9} {'~size':>8}")
    for p in plans:
        print(f"  {p.name:<16} {format_timestamp(p.start):>17} "
              f"{format_timestamp(p.end):>10} {format_timestamp(p.duration):>9} "
              f"{p.est_bytes / 1e6:>6.0f} MB")

    if not args.yes:
        answer = input("\nProceed with split? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted — nothing written.")
            return

    print()
    total = len(plans)
    split_recording(
        args.input, plans, out_dir,
        progress=lambda p, path: print(
            f"  [{p.index + 1}/{total}] wrote {path.name} "
            f"({path.stat().st_size / 1e6:.0f} MB)"),
    )
    print(f"\nDone — {total} chunks in {out_dir}. Raw recording untouched.")


if __name__ == "__main__":
    main()
