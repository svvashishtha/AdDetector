# ad-detector

An AI model that distinguishes **ads from regular content on a TV**, running on an
**edge device — an old Samsung Galaxy S21**. The phone sits in front of the TV,
watching through its **camera and microphone**, and detects in real time when an ad
is playing vs normal content.

**Underlying motivation:** prove that old devices can be repurposed for useful,
out-of-the-box ML tasks. Keep the budget low — free tools (Colab free tier,
open-source libraries) wherever possible; spend only where genuinely necessary.

> This README is **authoritative** for system design and build order. `plan/` is an
> execution log that references this ordering; if they ever disagree, this file wins.
> See [Documentation model](#documentation--planning-model).

---

## The core insight: one hard problem

Broadcast-TV detection and in-app OTT detection (YouTube pre-rolls etc.) look like
different problems but aren't. The real distinction is *what information you can access*:

- **If you control the stream/player** (broadcaster, CDN, your own app): ad boundaries
  are already known via stream metadata — SCTE-35 markers, HLS/DASH manifest tags, the
  player's own ad state. No ML needed; you just read the signal. YouTube's "skip in 5s"
  is the player reading its own ad flag, **not** computer vision.
- **If you are an outside observer** (a phone watching someone else's screen): you get
  **only pixels and audio, secondhand**. No metadata. This is a genuine ML inference
  problem. (Expecting an app to expose ad signals to an external observer is naive —
  it doesn't happen. DRM/FLAG_SECURE on OTT apps often blocks screen capture too.)

**Our setup is the second case**, so broadcast vs OTT is irrelevant to us — it's all
"signal-based detection from the outside," one hard problem.

## Signal strategy (locked)

**Audio is the primary signal. Video is secondary.**

- Audio classification is far lighter than video for edge devices.
- Ads carry strong audio signatures: loudness-normalized higher, compressed dynamic
  range, distinct jingles/voiceover density. The loudness/dynamic-range jump is the
  single best cheap feature.
- A camera pointed at a screen is noisy: glare, angle, moiré, refresh-rate flicker,
  ambient light. Audio via mic is degraded by room acoustics but still **more reliable
  than the camera** here.

Video cues (weak confirm, used only if audio underperforms): faster scene-cut frequency
during ads, black-frame/logo transitions at boundaries, channel logo ("bug")
disappearing during ad breaks, on-screen "Ad" markers.

**Plan:** audio-only baseline first; add a video branch only if audio alone is
insufficient. **But collect both audio and video from day one** — re-recording later
because we skipped video is the expensive mistake; storage is cheap.

## Hardware: Samsung S21 (locked)

The S21 is a 2021 flagship, not a weak device — capable GPU + dedicated NPU. This
**removes compute as a constraint**. The real constraints are **data quality and
accuracy**, not model size.

- **Runtime:** TFLite / LiteRT on Android. Mature, free, well-documented. NNAPI/GPU
  delegates exist, but the audio model is tiny — CPU is likely plenty. Don't optimize
  hardware acceleration early.
- **Model options open up:** YAMNet embeddings + light head, or a small custom CNN on
  log-mel spectrograms; even a small video branch (MobileNetV3-Lite) is feasible.
- **The same phone does data collection and deployment.** This kills the domain-gap
  problem: what we record (tinny TV-through-a-mic audio, camera-of-a-screen video) is
  exactly what we infer on. No train/deploy mismatch.

## Model approach (outlined, not locked)

- **v1:** binary audio classifier (ad vs content). Either YAMNet embeddings → small
  classifier head (fastest path to a baseline), or a compact CNN on log-mel
  spectrograms (more control). YAMNet is the lean first try; custom CNN is the fallback
  if YAMNet's features don't separate ads well.
- **Optional video branch later:** MobileNetV3-Lite on ~5fps sampled frames, fused with audio.
- **Temporal smoothing:** classify rolling windows, then majority-vote / HMM over the
  last N windows so output doesn't flicker at every scene cut. Steady state (mid-ad,
  mid-content) is easy; **the transition/boundary is the hard part** and where errors
  concentrate — and it's the moment we care about most.
- **Deployment:** int8 quantization, TFLite. Target small (<5–10 MB) though the S21
  doesn't force this.

## v2 — parked, but build extensibly (locked as future goal)

TV ad inventory is **finite and repetitive**. Exploit it with a two-tier system
(v2, NOT a change to the v1 classifier):

1. **Audio fingerprinting (Shazam-style):** library of known-ad fingerprints. Match
   incoming audio → instant, near-certain hit on a *known* ad.
2. **ML classifier fallback:** no fingerprint match → the classifier decides "is this
   ad-like" — generalizes to *unseen* ads.
3. **Auto-enrollment loop:** when the classifier confidently flags an unseen ad, add
   its fingerprint to the library. Next time it's an instant tier-1 hit.

**Why v2, not v1:** the fingerprinter is useless on day one (empty library — every ad
is unseen). The classifier bootstraps the fingerprint collection.

**Correction captured:** subtype labels and fingerprinting do NOT provide model
*explainability* — the model learns its own internal spectrogram features that can't
be read back out in our categories. Don't conflate metadata/fingerprinting with
interpretability.

**v1 implications:** log confident detections so they're ready to be fingerprinted
later; keep `audio.py` preprocessing as shared, importable code so v2 reuses it.

## Data discipline (locked — these prevent silent failure)

### Split by recording, never by clip
If you slice a recording into 2s windows and shuffle-split randomly, a window at 04:00
lands in train and 04:02 (nearly identical) lands in test → the model memorizes, test
scores look great, real performance tanks. **Whole recordings go entirely to one
bucket** (train OR val OR test). A 10-ad movie is fine *as long as the whole movie goes
to one set*. Implication: we need **many distinct recordings** to split cleanly — many
shorter sessions across channels/times beats one long session.

### Balance the training set only
Real-world ratio is mostly content, occasional ad. Handle class imbalance **during
training** (oversample ad windows, or class-weight the loss) — **only on the training
set**. Leave **val/test at natural, realistic ratios** (mostly content), because that's
what the phone actually faces. Balancing val/test would make the accuracy number lie.

**Decouple these two:** splitting is by recording (anti-leakage); imbalance is handled
by sampling/weighting within train (anti-bias). Don't solve imbalance by cherry-picking
which slices go where — that recreates leakage.

### Identical preprocessing, train and infer
The most common silent accuracy killer. Dataset building and live inference must
compute features **identically** — same sample rate, window size, hop, mel params.
Enforced structurally: **one shared config** (`config/pipeline.yaml`) + **one shared
`audio.py`** imported everywhere. Never two implementations.

## Eval strategy (locked)

- **Offline eval (primary, fast loop):** model runs **directly on held-out MP4 files** —
  no re-playing on a TV, no camera. Predict per window, compare to CSV labels.
  Scriptable, repeatable; ~90% of eval. Because the MP4s were recorded *through the
  phone*, this eval already includes camera/mic degradation — realistic, not cheating.
- **Live eval (final validation, infrequent):** phone in front of TV, real playback,
  end-to-end. Catches real-time effects offline eval misses — rolling-buffer timing,
  dropped frames, lag, thermal throttling. Slow/manual; used to *validate*, not *iterate*.
- **Keep dedicated recordings for live eval** that never touched training (like a test
  set, spent on the real-world run).
- **Stratified eval:** report accuracy *per ad subtype*, not just overall — catches
  weaknesses a single number hides.

## Collection pipeline (locked)

**Flow:** `record → split → distribute → label in parallel → merge → normalize → slice → Drive`

### Recording
- S21, continuous capture, stable framing of the TV. Capture at **full quality** —
  downsample in processing, never at capture (under-capturing is unrecoverable;
  downsampling keeps the original).
- Many sessions across channels/times/lighting for diversity.
- **Ad-variety risk:** finite ad inventory means you may record the same few spots
  repeatedly → model memorizes specific ads instead of "ad-ness." Consciously vary
  channels/times.

### Storage
- Raw MP4s → **old HDD** (single copy; acceptable for re-recordable TV footage, but a
  real single-point-of-failure tradeoff).
- **CSV labels → backed up properly (git/Drive)** — the irreplaceable artifact; never
  trust them to the HDD alone.
- Sliced training windows → **Google Drive** (for Colab).

### Splitting (separate script, NOT in the labeler)
- ffmpeg, **lossless** (`-c copy`), **keyframe-aligned**, **~30-min chunks**, **~30s
  overlap** between chunks (overlap via per-chunk seek — true overlap isn't native to
  ffmpeg's segment muxer).
- **Why split before labeling:** enables **parallel labeling** with a second person —
  each takes different chunks.
- **Ownership rule:** label any ad that *starts* in your chunk (the overlap ensures no
  boundary ad is orphaned).
- Naming/provenance: `rec007_chunk03` — every chunk traces to its source recording
  (needed for split-by-recording).
- **Keyframe honesty:** lossless cuts only land on keyframes, so actual cut points
  won't be exactly 30:00. The preview must show **real keyframe positions**, not
  idealized marks, or the preview lies.

### Labeling
Browser tool in [`labeler/`](labeler/README.md) — the ad-definition rule, subtypes, full
tool spec, and CSV format live in its README (keep it open while labeling). Mark **ads
only**; content = the gaps (inferred) — less clicking, fewer mistakes. Seek-heavy
workflow supported: scrub to find an ad, mark it, move on.

### Processing
- **Normalize first:** phone MP4s are often variable-framerate and 44.1/48kHz.
  Re-encode to **constant framerate** + standardized **sample rate** *before* slicing,
  or alignment breaks.
- **Audio/video sync:** keep them timestamp-locked from one source of truth; extracting
  separately risks drift.
- Sample video to **~5fps** (config), keep **audio dense** (smaller hop). Audio sample
  rate (kHz) and video frame rate (fps) are distinct knobs — kept separate in config.
- Slice into **2s windows** (configurable), each inherits its label.
- Provenance IDs so every window traces to its recording.

## Repo structure (locked)

Monorepo — the whole project context sits behind this one README, with
function-specific READMEs in subfolders.

```
ad-detector/
├── README.md            # this file: SYSTEM DESIGN + canonical BUILD ORDER (authoritative)
├── CLAUDE.md            # dense pointers for Claude + "don't relitigate" list
├── plan/                # EXECUTION LOG only (stateful checklists; references this README)
├── config/
│   └── pipeline.yaml    # THE shared config — read by everything
├── labeler/             # browser labeling tool (publishable standalone from its subfolder)
│   ├── src/labeler.ts   # logic (no DOM)
│   ├── src/ui.ts        # DOM wiring
│   └── README.md        # ad-definition rule + subtypes (on screen while labeling)
├── pipeline/            # Python: all data + model work
│   ├── adbreak/         # importable package = ALL real logic
│   │   ├── config.py    # loads config/pipeline.yaml → typed object
│   │   ├── audio.py     # mel features — SHARED by dataset-build AND inference
│   │   ├── video.py     # frame sampling
│   │   ├── splitting.py # keyframe-aligned lossless chunking
│   │   ├── slicing.py   # CSV + recording → labeled windows
│   │   ├── dataset.py   # split-by-recording, train-only balancing
│   │   ├── model.py     # architecture
│   │   └── infer.py     # inference + temporal smoothing
│   ├── scripts/         # THIN CLI entrypoints (~20 lines: parse args, call into adbreak/)
│   └── tests/
├── data/                # gitignored — recordings never committed
└── models/              # gitignored — trained artifacts never committed
```

**Structural principles (locked):**
- **Logic in the package, CLIs are thin** — same separation as the labeler (logic vs
  UI); here it's logic vs CLI. Testable and reusable (v2 fingerprinting imports `audio.py`).
- **One config file, both pipelines read it** — how "identical preprocessing" is
  *enforced structurally* rather than by discipline.
- **`audio.py` is shared, single-source.** Dataset building and live inference import
  the same mel function. Never two implementations.
- **Colab calls into the package** (`pip install -e`), doesn't copy-paste logic —
  prevents notebook/repo drift.
- **`data/` and `models/` gitignored.** Recordings live on the HDD; models are big
  binaries. Only code + config + labels in git.

## Documentation & planning model

Four doc types, **one source of truth each, no overlap:**

1. **`README.md`** (this file) — system design **and** canonical build order.
   **Authoritative.** (No separate DESIGN.md — deliberately folded in to avoid two sources.)
2. **`plan/`** — **execution log only.** Doesn't *define* sequence; it *references*
   this README's ordering. Resumable, stateful checklists so work can stop/start anytime.
   Format and step rules are in [`plan/README.md`](plan/README.md).
3. **`CLAUDE.md`** — dense pointers + "don't relitigate" list for fast orientation.
   Facts live once — CLAUDE.md points, never duplicates.
4. **Per-subfolder READMEs** — function-specific (e.g. `labeler/README.md` holds the
   ad-definition rule).

## Build order (canonical)

1. **Scaffold the repo** — this tree, docs, config stub, git init.
2. **Splitter** — `pipeline/scripts/split_recording.py` + logic in the package.
   Preview (length, approx size, real keyframe cut points) → wait for confirmation →
   progress while splitting → named chunks (`recNNN_chunkNN`).
3. **Labeler** — per `labeler/README.md` spec. Load MP4 → mark/edit/save ads with
   category → export CSV → re-import round-trips.
4. **Collection runs** — phone records while detection is built in parallel.
5. **Detection pipeline** — normalize/slice/dataset/train/eval (design to be detailed:
   exact model arch, buffer/smoothing params, runtime wiring, training notebook).
6. **On-device runtime** — TFLite on the S21, live eval.
7. **v2** — fingerprint tier + auto-enrollment (parked).

Execution status lives in [`plan/README.md`](plan/README.md).

## Scope guardrails (decided & rejected)

Rejected to keep scope tight — don't reintroduce without explicit discussion:
custom recording app, VLC-driven labeling, in-browser file splitting, frame-perfect
labeling tools, waveform view, keyboard-shortcut config, separate DESIGN.md,
`bumper` as its own label subtype.
