"""FL Studio mixer-track pan rule for stereo signals (the "Circular" law).

Reverse-engineered from rendered pan sweeps of FL Studio 20.8.3 and verified
against those renders to float32 precision.  See
``docs/结论_FL_Studio_Pan_Rule.md`` for the derivation and the evidence.

Notation
--------
``pan`` is the mixer-track pan in ``[-1, 1]`` (``-1`` hard left, ``0`` centre,
``+1`` hard right), and::

    theta = (pan + 1) * pi / 4
    A     = sqrt(2) * cos(theta)
    B     = sqrt(2) * sin(theta)

    pan <= 0 :  L' = A * ((1 + B)/2 * L + (1 - B)/2 * R)
                R' = B * R

    pan >= 0 :  L' = A * L
                R' = B * ((1 + A)/2 * R + (1 - A)/2 * L)

Properties
----------
* ``pan == 0`` is the identity.
* A mono input (``L == R``) collapses to ``(L', R') = L * sqrt(2) * (cos, sin)``:
  strictly equal power, ``+3.01 dB`` at the hard extremes.  This is the shape
  Image-Line documents as "Circular panning".
* A hard-panned input gets a boost above unity on the way to centre: with
  ``L == 1, R == 0`` the left output peaks at :data:`PEAK_GAIN` (+0.42 dB).
* A 100% pan of an arbitrary stereo pair is ``(L + R) / sqrt(2)`` in the panned
  channel and ``0`` in the other, i.e. the documented "mono-sum".
"""

from __future__ import annotations

import math

import numpy as np

__all__ = [
    "PEAK_GAIN",
    "PEAK_PAN",
    "SQRT2",
    "circular_gains",
    "gains",
    "matrix",
    "peak",
    "process",
    "theta",
]

SQRT2 = math.sqrt(2.0)


def theta(pan: float | np.ndarray) -> np.ndarray:
    """Map pan in ``[-1, 1]`` to ``theta`` in ``[0, pi/2]``."""
    return (np.asarray(pan, dtype=np.float64) + 1.0) * (math.pi / 4.0)


def circular_gains(pan: float | np.ndarray) -> tuple:
    """Return ``(A, B) = (sqrt(2)cos(theta), sqrt(2)sin(theta))``.

    These are the gains the law applies to a mono source; ``A**2 + B**2 == 2``.
    """
    th = theta(pan)
    return SQRT2 * np.cos(th), SQRT2 * np.sin(th)


def gains(pan: float | np.ndarray) -> tuple:
    """Return the four matrix entries ``(gLL, gLR, gRL, gRR)``."""
    p = np.asarray(pan, dtype=np.float64)
    a, b = circular_gains(p)
    left = p <= 0.0
    # Blend weight of the channel the signal is being panned towards.  It runs
    # from 1 at centre (pure own signal) to 1/2 at the extreme (pure mono sum).
    w = np.where(left, (1.0 + b) * 0.5, (1.0 + a) * 0.5)
    g_ll = np.where(left, a * w, a)
    g_lr = np.where(left, a * (1.0 - w), 0.0)
    g_rl = np.where(left, 0.0, b * (1.0 - w))
    g_rr = np.where(left, b, b * w)
    return g_ll, g_lr, g_rl, g_rr


def process(pan: float | np.ndarray, left, right) -> tuple:
    """Apply the pan rule to one or more stereo samples.

    Returns ``(left_out, right_out)``, broadcasting the three inputs together.
    """
    g_ll, g_lr, g_rl, g_rr = gains(pan)
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    return g_ll * left + g_lr * right, g_rl * left + g_rr * right


def matrix(pan: float | np.ndarray) -> np.ndarray:
    """Return the 2x2 gain matrix, shape ``(..., 2, 2)``.

    ``[L', R'] = matrix(pan) @ [L, R]``.
    """
    g_ll, g_lr, g_rl, g_rr = gains(pan)
    return np.stack(
        [np.stack([g_ll, g_lr], axis=-1), np.stack([g_rl, g_rr], axis=-1)], axis=-2
    )


def peak() -> tuple[float, float]:
    """Return ``(pan, gain)`` of the maximum gain any channel can reach.

    Maximising ``A(1+B)/2`` over ``pan <= 0`` gives ``sin(theta) = (sqrt(34) -
    sqrt(2))/8``, so the peak is algebraic and exact.
    """
    sin_theta = (math.sqrt(34.0) - math.sqrt(2.0)) / 8.0
    th = math.asin(sin_theta)
    a = SQRT2 * math.cos(th)
    b = SQRT2 * math.sin(th)
    return th * 4.0 / math.pi - 1.0, a * (1.0 + b) / 2.0


PEAK_PAN, PEAK_GAIN = peak()
