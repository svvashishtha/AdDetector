"""Dataset assembly: split-by-recording + train-only balancing.

Two decoupled rules (see root README, "Data discipline"):
- Whole recordings go entirely to one bucket (train OR val OR test) — anti-leakage.
- Class imbalance is handled by oversampling/class-weighting WITHIN train only;
  val/test keep natural, realistic ratios — anti-bias.

Not yet implemented — built in plan/05-detection.md.
"""
