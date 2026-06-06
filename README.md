# ad-detector

Real-time ad-vs-content detection that runs on a phone pointed at a TV.

A Samsung Galaxy S21 sits in front of a television, watches the screen through its
camera and microphone, and classifies in real time whether an advertisement or normal
programming is playing. Everything runs on-device.

The project is also a demonstration: a 2021 phone is enough to do useful, real-time ML
at the edge. It is built to run on free tooling (Google Colab, open-source libraries)
and commodity hardware.

## Status

In development. The data-collection pipeline is designed and being built; the detection
model is in design. See [Build order](#build-order) for sequencing and
[`plan/`](plan/README.md) for live execution status.

## How it works

The phone is an outside observer. It cannot read any app's internal ad state — it only
has the pixels and audio coming off the screen, so detection has to be inferred from the
signal itself. This is true whether the source is broadcast TV or a streaming app, which
is why the project treats them as a single problem rather than two.

Detection is **audio-first**. Audio is far cheaper to process at the edge than video,
and ads carry strong audio signatures — they are mastered louder, with compressed
dynamic range and dense voiceover/jingles. A camera aimed at a screen, by contrast,
fights glare, viewing angle, moiré, and refresh-rate flicker. Video is kept as a
secondary signal (scene-cut rate, channel-logo and black-frame transitions) and only
brought in if audio alone proves insufficient.

The classifier runs over short rolling audio windows, and predictions are smoothed over
time so the output doesn't flicker at every scene cut. Steady state is easy; the
ad/content boundary is the hard part, and it's the moment the system most needs to get
right.

## Architecture

Two pipelines share one preprocessing definition.

**Collection** turns recordings into labeled training data:

```
record → split → label (in parallel) → merge → normalize → slice → store
```

A recording is split into ~30-minute, keyframe-aligned chunks so it can be labeled by
more than one person at once. Labeling is done in a small browser tool (see
[`labeler/`](labeler/README.md)): only ads are marked, and everything unmarked is
treated as content. Labeled recordings are normalized to a constant frame rate and a
fixed sample rate, then sliced into fixed-length windows that each inherit their label.

**Detection** runs on the phone: capture → rolling audio window → preprocess →
classifier → temporal smoothing → ad/content state.

The two pipelines compute audio features from **the same code and the same config
file**. Mismatched preprocessing between training and inference is the most common cause
of a model that scores well offline and fails in the field; sharing one `audio.py` and
one `config/pipeline.yaml` makes that mismatch structurally impossible.

## Model

The first version is a binary audio classifier (ad vs content). Two candidate
approaches: YAMNet embeddings feeding a small classifier head (fastest route to a
baseline), or a compact CNN over log-mel spectrograms (more control). The model is
exported to TFLite with int8 quantization for on-device inference.

The S21 has a capable GPU and NPU, so model size is not the binding constraint — data
quality and accuracy are. Hardware acceleration (NNAPI/GPU delegates) is available but
unnecessary for a model this small; CPU inference is expected to be sufficient.

Because the same phone is used for both collection and deployment, training data already
contains the real-world degradation (through-the-mic audio, camera-of-a-screen video)
the model meets at inference. There is no train/deploy domain gap to close separately.

## Repository layout

```
ad-detector/
├── README.md            System design and build order (authoritative)
├── CLAUDE.md            Orientation notes for AI assistants
├── plan/                Execution log — stateful checklists, references this README
├── config/
│   └── pipeline.yaml    Shared preprocessing config, read by every component
├── labeler/             Browser-based labeling tool (standalone, publishable)
│   ├── src/
│   │   ├── labeler.ts   Segment logic — no DOM
│   │   └── ui.ts        DOM wiring
│   └── README.md        Labeling guide + ad definition
├── pipeline/            Python — all data and model work
│   ├── adbreak/         Importable package; all real logic lives here
│   │   ├── config.py    Loads config/pipeline.yaml into a typed object
│   │   ├── audio.py     Mel features — shared by dataset build and inference
│   │   ├── video.py     Frame sampling
│   │   ├── splitting.py Keyframe-aligned lossless chunking
│   │   ├── slicing.py   CSV + recording → labeled windows
│   │   ├── dataset.py   Split-by-recording, train-only balancing
│   │   ├── model.py     Model architecture
│   │   └── infer.py     Inference + temporal smoothing
│   ├── scripts/         Thin CLI entry points that call into adbreak/
│   └── tests/
├── data/                Recordings (git-ignored)
└── models/              Trained artifacts (git-ignored)
```

Two conventions keep the codebase maintainable:

- **Logic lives in the `adbreak/` package; CLIs and notebooks are thin.** Scripts parse
  arguments and call in. Colab installs the package (`pip install -e`) rather than
  copying code, so the notebook and the repo can't drift. The same separation lets v2
  reuse `audio.py` directly.
- **One config file feeds both pipelines.** It is the single source of truth for sample
  rate, window size, hop, mel parameters, video frame rate, and chunk length.

## Data handling

Three rules protect against models that look accurate but aren't:

- **Split train/validation/test by recording, never by window.** Adjacent windows from
  one recording are nearly identical; letting them fall on both sides of a split lets the
  model memorize instead of generalize. Whole recordings go to exactly one set. This is
  why the project favors many short, varied recordings over a few long ones.
- **Balance only the training set.** Class imbalance (mostly content, occasional ad) is
  handled during training via oversampling or class weighting. Validation and test sets
  keep their natural ad/content ratio, because that's what the phone actually faces — a
  balanced test set would report an accuracy the field won't reproduce.
- **Preprocess identically for training and inference** — enforced by the shared config
  and shared `audio.py` described above.

## Evaluation

Day-to-day evaluation runs the model directly against held-out MP4 files and compares
per-window predictions to the labels. It's fast, scriptable, and — because the files
were recorded through the phone — already reflects real camera and microphone
degradation. A separate set of recordings is reserved for this and never used in
training.

Final validation is run live: the phone in front of a TV, end to end. This catches
real-time effects the file-based path can't — buffer timing, dropped frames, latency,
thermal throttling. It's slow and manual, used to confirm rather than to iterate.

Accuracy is reported per ad subtype, not just overall, so weaknesses in a particular
category aren't hidden inside a single headline number.

## Build order

1. **Scaffold** the repository, docs, and config stub.
2. **Splitter** — `pipeline/scripts/split_recording.py`. Previews chunk boundaries
   (duration, approximate size, real keyframe cut points), waits for confirmation, then
   splits with progress output into named chunks (`recNNN_chunkNN`).
3. **Labeler** — the browser tool specified in [`labeler/README.md`](labeler/README.md).
4. **Collection** — recording begins while detection is built in parallel.
5. **Detection pipeline** — normalization, slicing, dataset assembly, training, offline
   eval. Model architecture and smoothing parameters to be finalized here.
6. **On-device runtime** — TFLite on the S21, live evaluation.
7. **v2** — see below.

This list is the authoritative build order. Live status for each item is tracked in
[`plan/README.md`](plan/README.md).

## Roadmap (v2)

TV ad inventory is finite and repetitive, which a later version can exploit with a
two-tier detector: an audio fingerprint library gives instant, near-certain matches on
ads it has seen before, and the classifier handles anything unrecognized. When the
classifier confidently identifies a new ad, its fingerprint is added to the library, so
the system recognizes it instantly next time.

This is deliberately deferred. The fingerprint library is empty on day one, so the
classifier has to come first and bootstrap it. v1 is built to feed this later — confident
detections are logged, and preprocessing is shared, importable code.

## Documentation

Each document has one job, to avoid duplicated facts that drift apart:

| File | Role |
|------|------|
| `README.md` | System design and build order — authoritative |
| `plan/` | Execution log; references this README's ordering |
| `CLAUDE.md` | Condensed orientation for AI assistants |
| `labeler/README.md`, `pipeline/README.md` | Component-specific detail |

If the execution log and this README ever disagree on design or ordering, this README
wins.

## Scope

The following were considered and deliberately left out to keep the project focused.
They shouldn't be reintroduced without explicit discussion: a custom recording app,
VLC-driven labeling, in-browser file splitting, frame-perfect labeling tools, a waveform
view, and configurable keyboard shortcuts.
