"""Inference + temporal smoothing (majority-vote / HMM over the last N windows).

Steady state is easy; transitions/boundaries are where errors concentrate and
what we care about most. Also: log confident detections so v2 can fingerprint
them later (auto-enrollment).

Not yet implemented — built in plan/05-detection.md.
"""
