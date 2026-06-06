"""v1 model architecture: binary audio classifier (ad vs content).

Candidates: YAMNet embeddings + small head (lean first try) or compact CNN on
log-mel spectrograms (fallback if YAMNet features don't separate ads well).
Subtypes are metadata, NOT a prediction target.

Not yet implemented — design detailed in plan/05-detection.md step 1.
"""
