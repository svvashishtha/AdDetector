"""CSV labels + normalized recording -> labeled 2s windows with provenance ids.

Normalize FIRST (constant framerate, standard sample rate) before slicing, or
audio/video alignment breaks. Every window must trace back to its source
recording (needed for split-by-recording).

Not yet implemented — built in plan/05-detection.md.
"""
