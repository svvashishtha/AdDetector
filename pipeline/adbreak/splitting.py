"""Lossless, keyframe-aligned chunking of raw recordings.

Why this exists (see root README, "Collection pipeline"):
- Split BEFORE labeling so two people can label different chunks in parallel.
- Lossless (`-c copy`) cuts can only land on keyframes, so planned cut points are
  snapped to REAL keyframe positions and the preview shows those — never
  idealized 30:00 marks ("keyframe honesty").
- Consecutive chunks overlap (config: splitting.overlap_seconds) so no boundary
  ad is orphaned; the ownership rule is "label any ad that *starts* in your
  chunk". True overlap isn't native to ffmpeg's segment muxer, so each chunk is
  cut with its own seek ("option B").
- Naming `recNNN_chunkNN` keeps provenance — every chunk (and later every sliced
  window) must trace to its source recording for split-by-recording.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class ChunkPlan:
    index: int
    name: str
    requested_start: float  # idealized grid position (i * stride)
    start: float            # REAL cut point: greatest keyframe <= requested_start
    end: float              # requested_start + chunk_seconds, clipped to duration
    est_bytes: int

    @property
    def duration(self) -> float:
        return self.end - self.start


# ---------------------------------------------------------------- probing

def probe_duration(path: Path) -> float:
    """Recording duration in seconds, via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def probe_keyframes(path: Path) -> list[float]:
    """Timestamps (seconds) of video keyframes, ascending.

    Reads packet flags rather than decoding frames — fast enough for long
    recordings.
    """
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "packet=pts_time,flags",
         "-of", "csv=print_section=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    keyframes = []
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) >= 2 and "K" in parts[1] and parts[0] not in ("", "N/A"):
            keyframes.append(float(parts[0]))
    keyframes.sort()
    return keyframes


# ---------------------------------------------------------------- planning (pure)

def plan_chunks(
    duration: float,
    keyframes: Sequence[float],
    chunk_seconds: float,
    overlap_seconds: float,
    rec_id: str,
    total_bytes: int = 0,
) -> list[ChunkPlan]:
    """Plan keyframe-aligned, overlapping chunks covering [0, duration].

    Chunk i's grid position is i * (chunk_seconds - overlap_seconds). Its start
    is snapped to the greatest keyframe <= grid position (what a lossless seek
    actually does); its end stays on the grid (grid + chunk_seconds), so the
    configured overlap with the next chunk is a guaranteed minimum, never less.
    """
    if chunk_seconds <= overlap_seconds:
        raise ValueError("chunk_seconds must exceed overlap_seconds")
    stride = chunk_seconds - overlap_seconds
    kfs = sorted(keyframes)

    def align(t: float) -> float:
        prior = [k for k in kfs if k <= t]
        return prior[-1] if prior else 0.0

    plans: list[ChunkPlan] = []
    i = 0
    while True:
        requested = i * stride
        if i > 0 and requested >= duration:
            break
        start = align(requested)
        end = min(requested + chunk_seconds, duration)
        if plans and end <= plans[-1].end:
            break  # tail already fully covered by the previous chunk
        est = int(total_bytes * (end - start) / duration) if duration else 0
        plans.append(ChunkPlan(
            index=i,
            name=chunk_name(rec_id, i),
            requested_start=requested,
            start=start,
            end=end,
            est_bytes=est,
        ))
        if end >= duration:
            break
        i += 1
    return plans


def chunk_name(rec_id: str, index: int) -> str:
    return f"{rec_id}_chunk{index:02d}"


# ---------------------------------------------------------------- cutting

def cut_chunk(src: Path, plan: ChunkPlan, out_dir: Path) -> Path:
    """Write one chunk losslessly. Seeking to plan.start (a keyframe) before the
    input with `-c copy` makes the cut land exactly there."""
    out_path = out_dir / f"{plan.name}.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-ss", f"{plan.start:.6f}", "-i", str(src),
         "-t", f"{plan.duration:.6f}",
         "-c", "copy", "-avoid_negative_ts", "make_zero",
         str(out_path)],
        check=True,
    )
    return out_path


def split_recording(
    src: Path,
    plans: Sequence[ChunkPlan],
    out_dir: Path,
    progress: Callable[[ChunkPlan, Path], None] | None = None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for plan in plans:
        path = cut_chunk(src, plan, out_dir)
        written.append(path)
        if progress:
            progress(plan, path)
    return written


def format_timestamp(seconds: float) -> str:
    """h:mm:ss.s for human-readable previews (storage stays raw seconds)."""
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:04.1f}"
