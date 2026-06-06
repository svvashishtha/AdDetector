# Plan 05 — Detection pipeline
Seq: 5/5 · Prev: 04-collection.md · Next: — (v2 fingerprinting parked; see README)
Design ref: README#model-approach-outlined-not-locked, README#eval-strategy-locked
Status: queued · last done: — · next: step 1 (design session first — internals are
NOT yet detailed: exact model arch, buffer/smoothing params, runtime wiring, notebook)

- [ ] 1. Detail the design: pick v1 arch (YAMNet-embeddings + head vs compact CNN on
         log-mel), smoothing scheme (majority vote vs HMM, N), normalize/slice specifics.
      done when: README's model section upgraded from "outlined" to "locked" with the
                 decisions + rationale; this plan rewritten with concrete build steps.
      reverse:   docs only; git revert.
- [ ] 2. Build normalize + slicing (adbreak/slicing.py, scripts/build_dataset.py):
         constant framerate + standard sample rate first, then 2s windows from CSVs,
         provenance ids.
      done when: a labeled chunk produces windows whose count/labels match the CSV by
                 hand-check; test_slicing.py passes.
      reverse:   generated data; delete outputs, raw + CSVs untouched.
- [ ] 3. Build dataset assembly (adbreak/dataset.py): split-by-recording, train-only
         balancing.
      done when: unit tests prove no recording spans buckets and val/test ratios are
                 natural.
      reverse:   code only; git revert.
- [ ] 4. Train v1 in Colab (scripts/train.py calls into the package via pip install -e).
      done when: a trained model beats the trivial always-content baseline on held-out
                 recordings.
      reverse:   models/ is gitignored; discard artifacts.
- [ ] 5. Offline eval (scripts/eval_offline.py): per-window predictions vs CSV on
         held-out MP4s; stratified per-subtype report.
      done when: eval runs end-to-end on a held-out recording and prints overall +
                 per-subtype metrics.
      reverse:   read-only over data; nothing to undo.
- [ ] 6. Quantize (int8 TFLite), build minimal Android runtime, live eval on the S21.
      done when: phone in front of TV flags ad breaks in real time; live results
                 roughly match offline eval.
      reverse:   app is additive; model artifacts disposable.
