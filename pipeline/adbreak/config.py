"""Load config/pipeline.yaml into typed objects.

THE shared config: every knob that must match between dataset building and live
inference lives in that one file and is accessed through this module. Never
hard-code these values elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# repo root = two levels up from this file's package (pipeline/adbreak/)
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "pipeline.yaml"


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int
    window_seconds: float
    hop_seconds: float
    n_fft: int
    hop_length: int
    n_mels: int


@dataclass(frozen=True)
class VideoConfig:
    fps: int


@dataclass(frozen=True)
class SplittingConfig:
    chunk_minutes: float
    overlap_seconds: float

    @property
    def chunk_seconds(self) -> float:
        return self.chunk_minutes * 60.0


@dataclass(frozen=True)
class PipelineConfig:
    audio: AudioConfig
    video: VideoConfig
    splitting: SplittingConfig


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> PipelineConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return PipelineConfig(
        audio=AudioConfig(**raw["audio"]),
        video=VideoConfig(**raw["video"]),
        splitting=SplittingConfig(**raw["splitting"]),
    )
