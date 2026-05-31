"""Clip Treatment — transformative-use toolkit for third-party clips, images, audio.

Locked production defaults (see approved_toolkit.json + skills/core/clip-treatments.md):
  - Copyrighted VIDEO → grade_cyan_orange + 1 of 8 approved frames (+ pitch_up_1st on audio if kept)
  - Copyrighted IMAGE → grade_crushed_warm + 1 of 8 approved frames
  - Copyrighted AUDIO → pitch_up_1st  (loudnorm I=-14 auto-applied)
  - Character images → EXEMPT (route through main flow's character cards)
"""
from tools.clip_treatment.clip_treatment import ClipTreatment

__all__ = ["ClipTreatment"]
