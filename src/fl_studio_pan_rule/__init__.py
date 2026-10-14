"""FL Studio's mixer-track pan rule for stereo signals, reverse-engineered.

The rule itself is in :mod:`fl_studio_pan_rule.rule`; :mod:`fl_studio_pan_rule.analysis`
reproduces the evidence from the renders bundled with this project (run
``fl-studio-pan-rule verify``).  Derivation and full evidence:
``docs/结论_FL_Studio_Pan_Rule.md``.
"""

from __future__ import annotations

from .analysis import (
    RENDER_2024,
    RENDER_OTHER,
    RENDER_SINE,
    SWEEP_FRAMES,
    format_report,
    invert_theta,
    load_sweep,
    mono_power,
    project_root,
    rejection,
    ripple,
    rule_fit,
    verify_all,
)
from .cli import main
from .rule import (
    PEAK_GAIN,
    PEAK_PAN,
    SQRT2,
    circular_gains,
    gains,
    matrix,
    peak,
    process,
    theta,
)
from .wav import Wav

__all__ = [
    "Wav",
    "SQRT2",
    "PEAK_GAIN",
    "PEAK_PAN",
    "theta",
    "circular_gains",
    "gains",
    "matrix",
    "process",
    "peak",
    "project_root",
    "load_sweep",
    "invert_theta",
    "rule_fit",
    "mono_power",
    "rejection",
    "ripple",
    "verify_all",
    "format_report",
    "RENDER_2024",
    "RENDER_SINE",
    "RENDER_OTHER",
    "SWEEP_FRAMES",
    "main",
]

__version__ = "0.1.0"
