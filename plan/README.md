# plan/ — execution log

This folder is the **execution log only**. It does not define sequence — the canonical
build order lives in the root [README](../README.md#build-order-canonical), which is
authoritative; if a plan doc disagrees with the README, the README wins.

## Dashboard

| Seq | Plan | Status | Next step |
|-----|------|--------|-----------|
| 1 | [01-scaffold](01-scaffold.md) | done | — |
| 2 | [02-splitter](02-splitter.md) | done | live-run on a real recording (needs ffmpeg installed) |
| 3 | [03-labeler](03-labeler.md) | done | — |
| 4 | [04-collection](04-collection.md) | queued | first recording session |
| 5 | [05-detection](05-detection.md) | queued | detail the design (model arch, smoothing, runtime) |

## Plan doc format

Each plan doc is a node in a doubly-linked list; the README's build order is the index.

```markdown
# Plan NN — <name>
Seq: N/total · Prev: <prev-doc> · Next: <next-doc>
Design ref: README#<section>
Status: <active|queued|done> · last done: <step> · next: <step>

- [x] 1. <step>
      done when: <clear completion criterion>
      reverse:   <how to undo — git, or "keep originals until verified", etc.>
```

Step rules:
- **Concrete & small** — one sitting's worth.
- **Checkable** — `[ ]`/`[x]` with an explicit **"done when:"** criterion, so a stopped
  step is unambiguously resumable.
- **Reversible** — a **"reverse:"** note per step; forces an escape hatch *before* acting.
- **Ordered** — dependencies clear via Prev/Next.
- **Status line at the top** of each plan doc — resuming = read one line, not the whole file.

Master dashboard (this file) = breadth, all of it, shallow. Sub-plans = depth, one
thing, detailed. Root README = design + why. CLAUDE.md = pointers.
