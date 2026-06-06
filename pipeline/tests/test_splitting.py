"""Tests for the pure chunk-planning logic (no ffmpeg needed)."""

import pytest

from adbreak.config import load_config
from adbreak.splitting import chunk_name, format_timestamp, plan_chunks

CHUNK = 1800.0  # 30 min
OVERLAP = 30.0


def kf_every(step: float, duration: float) -> list[float]:
    out, t = [], 0.0
    while t < duration:
        out.append(round(t, 3))
        t += step
    return out


def test_short_recording_single_chunk():
    plans = plan_chunks(600.0, kf_every(2.0, 600.0), CHUNK, OVERLAP, "rec001")
    assert len(plans) == 1
    assert plans[0].start == 0.0
    assert plans[0].end == 600.0
    assert plans[0].name == "rec001_chunk00"


def test_starts_snap_to_real_keyframes():
    keyframes = kf_every(2.0, 5400.0)
    plans = plan_chunks(5400.0, keyframes, CHUNK, OVERLAP, "rec001")
    for p in plans:
        assert p.start in keyframes or p.start == 0.0
        assert p.start <= p.requested_start


def test_overlap_is_a_guaranteed_minimum():
    # Keyframes every 7s: grid positions rarely land on a keyframe, so starts
    # snap earlier — overlap must never drop below the configured value.
    duration = 4 * CHUNK
    plans = plan_chunks(duration, kf_every(7.0, duration), CHUNK, OVERLAP, "rec001")
    assert len(plans) > 1
    for prev, nxt in zip(plans, plans[1:]):
        assert prev.end - nxt.requested_start >= OVERLAP
        assert prev.end - nxt.start >= OVERLAP  # snapping only widens overlap


def test_full_coverage_no_gaps():
    duration = 3.5 * CHUNK
    plans = plan_chunks(duration, kf_every(5.0, duration), CHUNK, OVERLAP, "rec001")
    assert plans[0].start == 0.0
    assert plans[-1].end == duration
    for prev, nxt in zip(plans, plans[1:]):
        assert nxt.start < prev.end  # overlap → no gap


def test_no_redundant_tail_chunk():
    # Duration just past one chunk: the tail is inside chunk 0's overlap zone
    # only if a second chunk would add nothing.
    duration = CHUNK + 100.0
    plans = plan_chunks(duration, kf_every(2.0, duration), CHUNK, OVERLAP, "rec001")
    assert plans[-1].end == duration
    ends = [p.end for p in plans]
    assert ends == sorted(set(ends)), "each chunk must extend coverage"


def test_sparse_keyframes_dont_break_monotonicity():
    duration = 3 * CHUNK
    plans = plan_chunks(duration, [0.0, 100.0, 2000.0, 4000.0], CHUNK, OVERLAP, "rec001")
    starts = [p.start for p in plans]
    assert starts == sorted(starts)
    assert plans[-1].end == duration


def test_chunk_seconds_must_exceed_overlap():
    with pytest.raises(ValueError):
        plan_chunks(100.0, [0.0], 30.0, 30.0, "rec001")


def test_chunk_naming_provenance():
    assert chunk_name("rec007", 3) == "rec007_chunk03"


def test_format_timestamp():
    assert format_timestamp(0.0) == "0:00:00.0"
    assert format_timestamp(3723.5) == "1:02:03.5"


def test_config_loads_and_matches_yaml():
    cfg = load_config()
    assert cfg.splitting.chunk_seconds == cfg.splitting.chunk_minutes * 60
    assert cfg.audio.sample_rate == 16000
    assert cfg.video.fps == 5
