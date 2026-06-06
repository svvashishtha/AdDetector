# ad-labeler

A single-purpose, self-contained browser tool for labeling ad segments in local TV
recordings. **Everything runs locally — the video never leaves your machine. No
uploads, no tracking.** MIT licensed.

Part of [ad-detector](../README.md) but publishable standalone from this folder.

---

## The ad-definition rule (KEEP THIS OPEN WHILE LABELING)

**Principle: label on the *signal*, not the legal category.** The system is an
*interruption detector* — tie labels to what it must detect: an interruption with a
detectable signal.

> Anything that interrupts the program the way a commercial break does — paid
> commercial spots, infomercials/shopping segments, and channel self-promos /
> "up next" / bumpers. In-program sponsorship counts as an ad **only if it carries a
> clear separable signal** (on-screen "Ad"/"Sponsored" marker, or a distinct
> audio/visual break). Brand mentions or logos baked into normal program flow stay
> **content**. Product placement stays content.
>
> **Tie-breaker:** if it interrupts viewing like a commercial break *and* has a
> detectable signal → ad; otherwise content.

Why interruption-based (not "paid-spots-only"): channel promos *look and sound* like
ads (loud, fast cuts, stings) and interrupt viewing identically, so they're labeled ad.
The test for in-program sponsorship is **"is there a separable signal?"** — a visible
"Ad" tag is detectable; a casual brand mention isn't (labeling undetectable cases just
injects noise).

### Subtypes (best-effort, never blocking)

| subtype | meaning | one-line example |
|---|---|---|
| `commercial` | paid product/service spot (the majority; **dropdown default**) | a 30s detergent spot between scenes |
| `promo` | channel advertising its own programming | "up next", "tonight at 9" |
| `sponsored` | in-program sponsorship that met the visible-signal bar | segment opens with a "Sponsored by X" card |
| `other` | anything ambiguous, incl. short bumpers/idents | a 3s channel ident sting between shows |

Rules:
- If the subtype isn't obvious in **~2 seconds** → mark `other`, move on. **Never let
  subtyping slow the main job.**
- `bumper` was deliberately dropped as its own category (too much "bumper or promo?"
  deliberation) — folded into `other`.
- **The v1 model trains binary (ad vs content).** Subtype is metadata carried along,
  NOT a prediction target and NOT model explainability. Its value: error analysis,
  diversity tracking (avoid a 90%-commercial set), future re-targeting (e.g. ignore
  promos, catch commercials), stratified eval.
- **Parallel-labeling consistency:** every labeler keeps this README open — drift
  between two people is worse than within one.
- Mark **ads only**; content = the gaps (inferred). Less clicking, fewer mistakes.
- **Ownership rule for chunked recordings:** label any ad that *starts* in your chunk
  (chunk overlap ensures no boundary ad is orphaned).

---

## Using the tool

```bash
npm ci           # .npmrc enforces ignore-scripts + exact versions
npm run build    # bundles src/ui.ts -> dist/app.js via esbuild
open index.html  # or just double-click it — no server needed
```

1. **Load a local MP4** (file picker — it stays on your machine).
2. Scrub/seek to find an ad — the seek-heavy workflow is the intended one; timestamps
   are exact regardless of how you reached the point.
3. **[Mark Ad Start]** / **[Mark Ad End]** capture the current video time into
   **editable** fields — **±0.5s nudge** buttons correct a delayed click; free-type
   (seconds or mm:ss) for bigger fixes.
4. Pick the subtype (defaults to `commercial`), **[Save Ad]** — the fields clear so
   the next ad starts clean.
5. Segment list: every row editable inline; ✕ deletes; the **mm:ss button next to a
   time seeks the video there to verify the mark**.
6. **Export CSV** when done; **Import CSV** to resume or fix an existing file.

### CSV format

```
ad_start,ad_end,type,source
134.5,164.0,commercial,rec001_chunk00.mp4
```

Times are **raw seconds** (machine-friendly; the UI displays mm:ss but never stores
it). `source` is the MP4 filename — it matters once dozens of CSVs exist. See
[sample.csv](sample.csv).

**Back up CSVs to git/Drive** — they're the irreplaceable artifact (raw footage is
re-recordable; labels aren't).

## Design notes

- **Browser-based, not VLC-driven (decided):** the HTML5 `<video>` element *is* the
  player — play/pause/seek/scrub for free, and `video.currentTime` gives the exact
  timestamp on click with no IPC. Driving VLC externally (HTTP interface + polling) is
  more moving parts and a looser timestamp. This tool is just buttons reading
  `currentTime`, not a video player.
- **Separation of concerns:** all logic in [`src/labeler.ts`](src/labeler.ts) (segment
  model, validation, nudge, CSV in/out — no DOM); DOM wiring in
  [`src/ui.ts`](src/ui.ts). The slicing pipeline can import the same types/logic.
- **Supply-chain hardening** (npm is under active attack — Shai-Hulud etc., which
  execute via install-time scripts):
  - `.npmrc` sets **`ignore-scripts=true`** — neuters the install-script vector.
    esbuild still works because its platform binary ships as an optionalDependency.
  - **Exact-pinned versions** (no `^`/`~`), committed lockfile, known-good
    slightly-aged releases — don't chase latest.
  - **Zero runtime dependencies** (vanilla DOM + HTML5 video); esbuild chosen over
    Vite specifically for the smaller transitive tree to audit.
  - Use `npm ci` (not `npm install`) so the lockfile is authoritative.

## Deliberately out of scope (v1)

Frame-perfect tools, waveform view, keyboard-shortcut config, in-browser file
splitting (splitting is a separate script — the browser can't cleanly write split
MP4s, and labeling marks ads regardless of where chunks were cut).
