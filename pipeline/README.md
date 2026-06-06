# pipeline/ — Python data + model work

All real logic lives in the importable **`adbreak/`** package; **`scripts/`** are thin
CLI entrypoints (~20 lines: parse args, call into the package). Colab notebooks
`pip install -e` this package and call into it — never copy logic into a notebook.

Design + rationale: see the [root README](../README.md) (authoritative).

## Setup

```bash
cd pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

`ffmpeg`/`ffprobe` must be on PATH for the splitter (`brew install ffmpeg` on macOS).

## Commands

```bash
# run tests
pytest

# run a single test
pytest tests/test_splitting.py -k test_name

# split a recording into ~30-min lossless, keyframe-aligned, overlapping chunks
# (previews real keyframe cut points and waits for confirmation before writing)
python scripts/split_recording.py /path/to/recording.mp4 --rec-id rec001
```

## Modules

| module | role |
|---|---|
| `adbreak/config.py` | loads `config/pipeline.yaml` → typed object. The ONLY way to read pipeline knobs. |
| `adbreak/audio.py` | mel features — **shared by dataset-build AND inference**, single source. |
| `adbreak/video.py` | ~5fps frame sampling (secondary signal; built only if needed). |
| `adbreak/splitting.py` | keyframe-aligned lossless chunking with overlap. |
| `adbreak/slicing.py` | CSV labels + recording → labeled 2s windows with provenance ids. |
| `adbreak/dataset.py` | split-by-recording, train-only balancing. |
| `adbreak/model.py` | v1 binary audio classifier. |
| `adbreak/infer.py` | inference + temporal smoothing; logs confident hits for v2 fingerprinting. |
