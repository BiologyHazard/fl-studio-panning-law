"""Verification of :mod:`fl_studio_pan_rule.rule` against the FL Studio renders.

The renders live in the two dated directories next to this project.  Four checks
are implemented, each of which can fail independently:

``rule_fit``    the law reproduces ``test_pan_2024-09-19.wav`` (input L=1, R=0)
``mono_power``  a mono input stays strictly equal-power (``test_sinewave.wav``)
``rejection``   the law does NOT fit a render made under a different pan law
                (``test_dc.wav``) -- the negative control
``ripple``      characterises the residual wobble of the automation timeline
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from . import rule
from .wav import Wav

__all__ = [
    "project_root",
    "SWEEP_FRAMES",
    "RENDER_2024",
    "RENDER_SINE",
    "RENDER_OTHER",
    "load_sweep",
    "invert_theta",
    "rule_fit",
    "mono_power",
    "rejection",
    "ripple",
    "verify_all",
    "format_report",
]

SWEEP_FRAMES = 384000  # 8.000 s at 48 kHz = the length of the DC source
RENDER_2024 = ("2024-09-19测试", "test_pan_2024-09-19.wav")
RENDER_SINE = ("2023-06-21测试", "test_sinewave.wav")
RENDER_OTHER = ("2023-06-21测试", "test_dc.wav")

K = 1.0 / math.sqrt(2.0)
THETA_PEAK = (rule.PEAK_PAN + 1.0) * math.pi / 4.0
QUARTER_PI = math.pi / 4.0


def project_root(start: str | Path | None = None) -> Path:
    """Walk up from ``start`` (default: this file) to the project root."""
    here = Path(start or __file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError("project root (pyproject.toml) not found")


def render(*parts: str) -> Path:
    """Absolute path of a bundled render."""
    return project_root().joinpath(*parts)


def load_sweep(path: str | Path, frames: int = SWEEP_FRAMES) -> tuple:
    """Return ``(left, right)`` covering the swept part of a render."""
    samples = Wav(path).samples()
    return samples[:frames, 0], samples[:frames, 1]


def _left_half_response(theta: np.ndarray) -> np.ndarray:
    """``gLL`` on the left half of the sweep: ``cos(t) * (1/sqrt(2) + sin(t))``."""
    return np.cos(theta) * (K + np.sin(theta))


def _bisect(target: np.ndarray, lo, hi, decreasing: bool) -> np.ndarray:
    lo = np.broadcast_to(np.asarray(lo, dtype=np.float64), target.shape).copy()
    hi = np.broadcast_to(np.asarray(hi, dtype=np.float64), target.shape).copy()
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        value = _left_half_response(mid)
        # `move_up` means the root is above `mid`
        move_up = value > target if decreasing else value < target
        lo = np.where(move_up, mid, lo)
        hi = np.where(move_up, hi, mid)
    return 0.5 * (lo + hi)


def invert_theta(left: np.ndarray, mid: int | None = None) -> np.ndarray:
    """Recover ``theta(i)`` from a hard-left-input render.

    On the right half ``L = sqrt(2) cos(theta)`` is monotonic.  On the left half
    ``L = cos(theta)(1/sqrt(2) + sin(theta))`` rises to ``1.0499`` at ``theta*``
    and falls back to ``1.0`` at ``pi/4``, so the branch is chosen from the
    position of the observed maximum (which is exactly where ``theta == theta*``).
    """
    left = np.asarray(left, dtype=np.float64)
    n = len(left)
    mid = n // 2 if mid is None else mid

    out = np.empty(n)
    out[mid:] = np.arccos(np.clip(left[mid:] / rule.SQRT2, -1.0, 1.0))

    i_peak = int(np.argmax(left[:mid])) + 1
    out[:i_peak] = _bisect(left[:i_peak], 0.0, THETA_PEAK, decreasing=False)
    out[i_peak:mid] = _bisect(left[i_peak:mid], THETA_PEAK, QUARTER_PI, decreasing=True)
    return out


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def rule_fit(path: str | Path | None = None, frames: int = SWEEP_FRAMES) -> dict:
    """Reproduce the hard-left-input render under two candidate pan timelines.

    Also checks the *parameter-free* relation the law imposes between the two
    output channels on the right half.  There ``A == L`` and ``B == sqrt(2 - L**2)``,
    so the law predicts ``R`` from the measured ``L`` alone::

        R = (1 - L) * sqrt(2 - L**2) / 2

    with no fitted constant at all.
    """
    path = Path(path) if path else render(*RENDER_2024)
    left, right = load_sweep(path, frames)
    nominal = 2.0 * np.arange(frames, dtype=np.float64) / (frames - 1) - 1.0
    recovered = invert_theta(left)

    result = {"path": str(path), "frames": frames, "timelines": {}}
    for name, pan in (
        ("nominal_linear_ramp", nominal),
        ("theta_from_render", recovered * 4.0 / math.pi - 1.0),
    ):
        out_left, out_right = rule.process(pan, 1.0, 0.0)
        err_left = np.abs(out_left - left)
        err_right = np.abs(out_right - right)
        loud = np.abs(left) > 0.1
        result["timelines"][name] = {
            "L_max_abs": float(err_left.max()),
            "L_rms": float(np.sqrt((err_left**2).mean())),
            "L_max_rel": float((err_left[loud] / np.abs(left[loud])).max()),
            "R_max_abs": float(err_right.max()),
            "R_rms": float(np.sqrt((err_right**2).mean())),
        }

    # law-specific, parameter-free prediction of R from L on the right half
    second = slice(frames // 2, frames)
    predicted_right = (1.0 - left[second]) * np.sqrt(
        np.maximum(2.0 - left[second] ** 2, 0.0)
    ) / 2.0
    err = np.abs(predicted_right - right[second])
    loud = np.abs(right[second]) > 0.1
    result["closed_form_R_from_L"] = {
        "R_max_abs": float(err.max()),
        "R_max_rel": float((err[loud] / np.abs(right[second][loud])).max()),
        "n": int(frames - frames // 2),
    }
    return result


def mono_power(path: str | Path | None = None, window: int = 480) -> dict:
    """For a mono input the law must give the constant power ``2 * s**2``."""
    path = Path(path) if path else render(*RENDER_SINE)
    samples = Wav(path).samples()
    left, right = samples[:, 0], samples[:, 1]
    windows = len(left) // window
    peak_left = np.abs(left[: windows * window].reshape(windows, window)).max(axis=1)
    peak_right = np.abs(right[: windows * window].reshape(windows, window)).max(axis=1)
    usable = (peak_left > 0.02) & (peak_right > 0.02)
    power = peak_left[usable] ** 2 + peak_right[usable] ** 2
    return {
        "path": str(path),
        "window_frames": window,
        "windows": int(usable.sum()),
        "power_mean": float(power.mean()),
        "power_std": float(power.std()),
        "power_min": float(power.min()),
        "power_max": float(power.max()),
        "relative_spread": float((power.max() - power.min()) / power.mean()),
        "implied_source_amplitude": float(math.sqrt(power.mean() / 2.0)),
    }


def rejection(path: str | Path | None = None) -> dict:
    """A render made under a *different* pan law must be rejected.

    ``test_dc.wav`` is an all-positive (DC) render whose right channel is exactly
    zero below centre, so the law's input is again ``(a, 0)``.  Its peak ratio
    ``L/R`` is then a fingerprint: ``1.4848`` for this law (because of the bump),
    ``1.4142`` for any law without it.
    """
    path = Path(path) if path else render(*RENDER_OTHER)
    samples = Wav(path).samples()
    left, right = samples[:, 0], samples[:, 1]
    frames = len(left)

    nominal = 2.0 * np.arange(frames, dtype=np.float64) / (frames - 1) - 1.0
    model_left, model_right = rule.process(nominal, 1.0, 0.0)
    # least-squares amplitude for the law's shape, so the comparison is fair
    amplitude = float(
        (left * model_left + right * model_right).sum()
        / (model_left**2 + model_right**2).sum()
    )
    residual = np.concatenate(
        [amplitude * model_left - left, amplitude * model_right - right]
    )

    half = frames // 2
    return {
        "path": str(path),
        "frames": frames,
        "observed_peak_ratio": float(left.max() / right.max()),
        "rule_peak_ratio": float(rule.PEAK_GAIN / (rule.SQRT2 / 2.0)),
        "no_bump_peak_ratio": float(1.0 / (rule.SQRT2 / 2.0)),
        "left_flat_below_centre": bool(np.all(np.diff(left[:half]) == 0.0)),
        "fitted_amplitude": amplitude,
        "residual_rms": float(np.sqrt((residual**2).mean())),
    }


def ripple(path: str | Path | None = None, frames: int = SWEEP_FRAMES,
           sample_rate: int = 48000) -> dict:
    """Measure how far the rendered automation timeline departs from linear.

    Uses the *forward* residual ``measured - law(nominal linear ramp)``, which
    needs no inversion and is therefore well conditioned: recovering ``theta``
    from ``L`` instead would divide by ``dL/dtheta``, which vanishes both at the
    peak of the left half and at hard right, turning float32 rounding into
    apparent wobble.  The right half is used because ``dL/dtheta`` is largest
    there apart from the very end.
    """
    left, _ = load_sweep(path if path else render(*RENDER_2024), frames)
    nominal = 2.0 * np.arange(frames, dtype=np.float64) / (frames - 1) - 1.0
    modelled, _ = rule.process(nominal, 1.0, 0.0)
    residual = (left - modelled)[frames // 2 :]

    centred = residual - residual.mean()
    autocorr = np.correlate(centred, centred, mode="full")[len(centred) - 1 :]
    autocorr /= autocorr[0]
    period = max(range(100, 20000), key=lambda lag: autocorr[lag])
    ptp = float(residual.max() - residual.min())
    return {
        "residual_ptp": ptp,
        "residual_max_abs": float(np.abs(residual).max()),
        "residual_rms": float(np.sqrt((residual**2).mean())),
        "residual_ptp_db": float(20.0 * math.log10(ptp)),
        "dominant_period_frames": int(period),
        "dominant_period_ms": float(period / sample_rate * 1000.0),
    }


def verify_all() -> dict:
    """Run every check and return the results."""
    left, _ = load_sweep(render(*RENDER_2024))
    return {
        "rule_fit": rule_fit(),
        "mono_power": mono_power(),
        "rejection": rejection(),
        "ripple": ripple(),
        "peak": {"pan": rule.PEAK_PAN, "gain": rule.PEAK_GAIN},
    }


def format_report(results: dict) -> str:
    """Render :func:`verify_all` output as a human-readable report."""
    lines: list[str] = []

    fit = results["rule_fit"]
    lines.append(f"[1] rule fit vs {Path(fit['path']).name}  (input L=1, R=0)")
    for name, r in fit["timelines"].items():
        lines.append(
            f"      pan timeline {name:22s} L max|err| {r['L_max_abs']:.3e}  "
            f"rms {r['L_rms']:.3e}  max rel {r['L_max_rel']:.2e}  "
            f"R max|err| {r['R_max_abs']:.3e}"
        )
    cf = fit["closed_form_R_from_L"]
    lines.append(
        f"      closed form R = (1-L)*sqrt(2-L^2)/2 on the right half "
        f"({cf['n']} frames): R max|err| {cf['R_max_abs']:.3e}  "
        f"max rel {cf['R_max_rel']:.2e}"
    )

    mp = results["mono_power"]
    lines.append(f"[2] mono constant power vs {Path(mp['path']).name}")
    lines.append(
        f"      L'^2+R'^2 mean {mp['power_mean']:.6f} +- {mp['power_std']:.2e}  "
        f"spread {mp['relative_spread']:.2e}  "
        f"=> source amplitude {mp['implied_source_amplitude']:.6f}"
    )

    rj = results["rejection"]
    rejected = abs(rj["observed_peak_ratio"] - rj["no_bump_peak_ratio"]) < 1e-3
    lines.append(f"[3] negative control vs {Path(rj['path']).name}")
    lines.append(
        f"      L/R peak ratio {rj['observed_peak_ratio']:.6f}  "
        f"(this law {rj['rule_peak_ratio']:.6f}, no-bump "
        f"{rj['no_bump_peak_ratio']:.6f})"
    )
    lines.append(
        f"      left channel flat below centre: {rj['left_flat_below_centre']}  "
        f"law residual rms {rj['residual_rms']:.4f}  "
        f"=> {'REJECTED' if rejected else 'unexpectedly consistent'}"
    )

    rp = results["ripple"]
    lines.append("[4] automation-timeline ripple (not part of the law)")
    lines.append(
        f"      forward residual ptp {rp['residual_ptp']:.3e} "
        f"({rp['residual_ptp_db']:.1f} dB)  rms {rp['residual_rms']:.3e}"
    )
    lines.append(
        f"      dominant period {rp['dominant_period_frames']} frames = "
        f"{rp['dominant_period_ms']:.3f} ms"
    )

    pk = results["peak"]
    lines.append("[5] analytic peak of the law")
    lines.append(
        f"      gain {pk['gain']:.12f} at pan {pk['pan']:.9f} = "
        f"{20 * math.log10(pk['gain']):+.4f} dB  (gain > 1 for pan in "
        f"[{-0.519251:.6f}, 0])"
    )
    return "\n".join(lines)
