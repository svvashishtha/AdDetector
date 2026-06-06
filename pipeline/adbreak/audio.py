"""Mel-spectrogram features — SHARED by dataset building AND live inference.

This is the single source of truth for audio preprocessing ("identical
preprocessing, train and infer"). Never reimplement these features elsewhere;
import from here. v2 fingerprinting will reuse this module too.

Not yet implemented — built in plan/05-detection.md.
"""
