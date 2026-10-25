"""Generate every figure used by the report, and optionally print the residuals.

Usage::

    uv run python scripts/make_figures.py            # figures only
    uv run python scripts/make_figures.py --stats    # figures + residual table

Renders live in ``output-wav-files/``: input is ``L = 1, R = 0`` and the pan sweeps
linearly from -100% to +100% over 8 s.

The pan law only fixes the single-channel gains ``(gL, gR)``::

    Circular    gL = sqrt(2)*cos(theta),  gR = sqrt(2)*sin(theta),  theta = (p+1)*pi/4
    Triangular  gL = 1 - max(p, 0),       gR = 1 + min(p, 0)

The implementation decides how the two channels are mixed::

    Mixer        p <= 0: L' = gL*[(1+gR)/2*L + (1-gR)/2*R],  R' = gR*R
                 p >= 0: L' = gL*L,                          R' = gR*[(1+gL)/2*R + (1-gL)/2*L]
    Channel      L' = gL*L,  R' = gR*R    (plain balance, no cross-mixing)

All figure text is English; symbols are mathtext.
"""

from __future__ import annotations

import argparse
import wave
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output-wav-files"
FIGURE_DIR = ROOT / "images"

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 220,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "figure.constrained_layout.use": True,
        "mathtext.fontset": "cm",
    }
)

COLOR_LEFT = "#c0392b"
COLOR_RIGHT = "#1f6fb4"
COLOR_MODEL = "0.72"
COLOR_ACCENT = "#2f7d32"

Gains = Callable[[np.ndarray], "tuple[np.ndarray, np.ndarray]"]
Implementation = Callable[
    [np.ndarray, "tuple[np.ndarray, np.ndarray]"], "tuple[np.ndarray, np.ndarray]"
]


# --------------------------------------------------------------------------- data


def load_render(name: str) -> np.ndarray:
    """Read a 32-bit float stereo WAV and return an ``(n, 2)`` float64 array."""
    path = OUTPUT_DIR / f"{name} Panning.wav"
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getnchannels() != 2:
            raise ValueError(f"stereo only: {path}")
        if wav_file.getformat() != wave.WAVE_FORMAT_IEEE_FLOAT:
            raise ValueError(f"32-bit float WAV only: {path}")
        raw = wav_file.readframes(wav_file.getnframes())
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)


def pan_grid(n_frames: int) -> np.ndarray:
    return np.arange(n_frames) / (n_frames - 1) * 2 - 1


# -------------------------------------------------------------------------- model


def circular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta = (pan + 1) * np.pi / 4
    return np.sqrt(2) * np.cos(theta), np.sqrt(2) * np.sin(theta)


def triangular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return 1 - np.maximum(pan, 0), 1 + np.minimum(pan, 0)


def mixer(
    pan: np.ndarray, gains: tuple[np.ndarray, np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Mixer track: the far channel is mixed into the near one, 100% is the mono sum."""
    g_left, g_right = gains
    to_left = pan <= 0
    left = np.where(to_left, g_left * (1 + g_right) / 2, g_left)
    right = np.where(to_left, 0.0, g_right * (1 - g_left) / 2)
    return left, right


def channel(
    pan: np.ndarray, gains: tuple[np.ndarray, np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Channel pan: plain balance. With ``L=1, R=0`` only the left output is non-zero."""
    g_left, _ = gains
    return g_left, np.zeros_like(g_left)


CASES: dict[str, tuple[str, str, Gains, Implementation]] = {
    "mixer-circular": (
        "Mixer Circular",
        "Mixer $\\times$ Circular",
        circular_gains,
        mixer,
    ),
    "mixer-triangular": (
        "Mixer Triangular",
        "Mixer $\\times$ Triangular",
        triangular_gains,
        mixer,
    ),
    "channel-circular": (
        "Audio Clip Circular",
        "Channel $\\times$ Circular",
        circular_gains,
        channel,
    ),
    "channel-triangular": (
        "Audio Clip Triangular",
        "Channel $\\times$ Triangular",
        triangular_gains,
        channel,
    ),
}


# --------------------------------------------------------------------- fig. 1-5


def figure_law() -> Path:
    pan = np.linspace(-1, 1, 4001)
    circ_left, circ_right = circular_gains(pan)
    tri_left, tri_right = triangular_gains(pan)

    figure, (gain_axis, shape_axis) = plt.subplots(1, 2, figsize=(11, 4.4))

    gain_axis.plot(pan, circ_left, color=COLOR_LEFT, label="Circular $g_L$")
    gain_axis.plot(pan, circ_right, color=COLOR_RIGHT, label="Circular $g_R$")
    gain_axis.plot(pan, tri_left, color=COLOR_LEFT, ls="--", label="Triangular $g_L$")
    gain_axis.plot(pan, tri_right, color=COLOR_RIGHT, ls="--", label="Triangular $g_R$")
    gain_axis.axhline(1.0, color="0.55", lw=0.8, zorder=0)
    gain_axis.set(
        xlabel="pan $p$",
        ylabel="single-channel gain",
        title="Gains of the two pan laws",
    )
    gain_axis.xaxis.set_major_locator(MultipleLocator(0.5))
    gain_axis.legend(fontsize=9, ncols=2)

    shape_axis.plot(circ_left, circ_right, color=COLOR_ACCENT, lw=2.0, label="Circular")
    shape_axis.plot(tri_left, tri_right, color="#a0522d", lw=2.0, label="Triangular")
    shape_axis.set(
        xlabel="$g_L$",
        ylabel="$g_R$",
        title="Trajectory of $(g_L, g_R)$ over the pan range",
        aspect="equal",
        xlim=(-0.18, 1.62),
        ylim=(-0.12, 1.62),
    )
    shape_axis.legend(loc="upper right")
    for label, p, offset, align in [
        ("hard left", -1, (-12, 10), "right"),
        ("center", 0, (8, 6), "left"),
        ("hard right", 1, (8, 6), "left"),
    ]:
        theta = (p + 1) * np.pi / 4
        shape_axis.plot(
            [np.sqrt(2) * np.cos(theta)],
            [np.sqrt(2) * np.sin(theta)],
            "o",
            color=COLOR_ACCENT,
            ms=5,
        )
        shape_axis.annotate(
            label,
            (np.sqrt(2) * np.cos(theta), np.sqrt(2) * np.sin(theta)),
            textcoords="offset points",
            xytext=offset,
            ha=align,
            fontsize=9,
        )
    return save(figure, "fig01-law.png")


def figure_combinations() -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for axis, case in zip(axes.flat, CASES.values()):
        name, title, gains, model = case
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))

        axis.plot(
            pan, measured[:, 0], color=COLOR_LEFT, lw=1.2, label="left (measured)"
        )
        axis.plot(
            pan, measured[:, 1], color=COLOR_RIGHT, lw=1.2, label="right (measured)"
        )
        axis.plot(pan, left, color=COLOR_MODEL, lw=4.0, zorder=0, label="model")
        axis.plot(pan, right, color=COLOR_MODEL, lw=4.0, zorder=0)
        axis.axhline(1.0, color="0.45", lw=0.8, ls=":", zorder=0)
        axis.set_title(title, fontsize=11)
        axis.set_xlim(-1, 1)
        axis.set_ylim(-0.02, 1.5)
        axis.xaxis.set_major_locator(MultipleLocator(0.5))

    for axis in axes[1]:
        axis.set_xlabel("pan $p$")
    for axis in axes[:, 0]:
        axis.set_ylabel("output  ($L=1$, $R=0$)")
    axes[0, 0].legend(loc="upper right", fontsize=9)
    return save(figure, "fig02-combinations.png")


def figure_peak() -> Path:
    pan = np.linspace(-1, 0, 4001)
    theta = (pan + 1) * np.pi / 4
    gain = np.sqrt(2) * np.cos(theta) * (1 + np.sqrt(2) * np.sin(theta)) / 2

    peak_theta = np.arcsin((np.sqrt(34) - np.sqrt(2)) / 8)
    peak_pan = peak_theta * 4 / np.pi - 1
    peak_gain = (
        np.sqrt(2) * np.cos(peak_theta) * (1 + np.sqrt(2) * np.sin(peak_theta)) / 2
    )
    crossing = pan[np.argmax(gain >= 1.0)]

    figure, axis = plt.subplots(figsize=(8, 4.4))
    axis.plot(pan, gain, color=COLOR_LEFT, lw=2.0, label="$L'$ for $L=1,\\ R=0$")
    axis.axhline(1.0, color="0.4", lw=0.9)
    axis.fill_between(pan, 1.0, gain, where=gain > 1.0, color=COLOR_LEFT, alpha=0.15)
    axis.plot([peak_pan], [peak_gain], "o", color=COLOR_LEFT, ms=6)
    axis.annotate(
        f"peak ${peak_gain:.7f}$ at $p={peak_pan:.6f}$  ($+0.4229$ dB)\n"
        f"$L'>1$ for $p\\in[{crossing:.4f},\\,0]$",
        xy=(peak_pan, peak_gain),
        xytext=(peak_pan - 0.40, 1.122),
        ha="left",
        va="top",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "0.35"},
    )
    axis.set(
        xlabel="pan $p$",
        ylabel="$L'$",
        title="Mixer $\\times$ Circular: the only combination that overshoots 0 dB",
        xlim=(-1, 0),
        ylim=(0.68, 1.13),
    )
    axis.legend(loc="lower right")
    return save(figure, "fig03-peak.png")


def figure_residual() -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(11, 6), sharex=True)
    for axis, case in zip(axes.flat, CASES.values()):
        name, title, gains, model = case
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))

        residual_left = measured[:, 0] - left
        residual_right = measured[:, 1] - right
        axis.plot(pan, residual_left * 1e6, color=COLOR_LEFT, lw=0.9, label="$L'$")
        if np.any(residual_right):
            axis.plot(
                pan, residual_right * 1e6, color=COLOR_RIGHT, lw=0.9, label="$R'$"
            )
        axis.set_title(title, fontsize=11)
        axis.set_xlim(-1, 1)
        axis.xaxis.set_major_locator(MultipleLocator(0.5))

    for axis in axes[1]:
        axis.set_xlabel("pan $p$")
    for axis in axes[:, 0]:
        axis.set_ylabel("measured $-$ model  ($\\times10^{-6}$)")
    axes[1, 1].legend(loc="upper left", fontsize=9)
    return save(figure, "fig04-residual.png")


def figure_spectrum() -> Path:
    """Turn the forward residual into a pan deviation to expose the automation error."""
    measured = load_render("Mixer Circular")
    n_frames = len(measured)
    pan = pan_grid(n_frames)
    left, _ = mixer(pan, circular_gains(pan))
    residual = measured[:, 0] - left

    slope = np.gradient(left, pan)
    deviation = residual / np.where(np.abs(slope) > 1e-3, slope, np.nan)

    windowed = np.nan_to_num(deviation) * np.hanning(n_frames)
    spectrum = np.abs(np.fft.rfft(windowed))
    spectrum[:5] = 0
    index = int(np.argmax(spectrum))
    frequency = index * 48000 / n_frames

    figure, (time_axis, freq_axis) = plt.subplots(1, 2, figsize=(11, 4.2))
    zoom = slice(0, 4800)
    time_axis.plot(
        np.arange(4800) / 48, deviation[zoom] * 1e3, color=COLOR_LEFT, lw=1.0
    )
    time_axis.set(
        xlabel="time (ms)",
        ylabel="actual $-$ nominal pan  ($\\times10^{-3}$)",
        title="Automation error, first 100 ms",
        xlim=(0, 100),
    )
    time_axis.axvline(750 / 48, color="0.4", lw=0.8, ls="--")
    time_axis.annotate(
        "15.625 ms",
        (750 / 48, 0.045),
        textcoords="offset points",
        xytext=(4, 0),
        fontsize=9,
    )

    freqs = np.arange(len(spectrum)) * 48000 / n_frames
    freq_axis.semilogy(freqs[5:], spectrum[5:], lw=0.9)
    freq_axis.set(
        xlabel="frequency (Hz)",
        ylabel="magnitude",
        title="Spectrum of the automation error",
        xlim=(0, 400),
    )
    freq_axis.axvline(frequency, color=COLOR_LEFT, lw=1.0, ls="--")
    freq_axis.annotate(
        f"${frequency:.2f}$ Hz",
        (frequency, spectrum[index]),
        textcoords="offset points",
        xytext=(6, 2),
        fontsize=9,
    )
    return save(figure, "fig05-spectrum.png")


# ------------------------------------------------------------------------ helpers


def save(figure: plt.Figure, name: str) -> Path:
    FIGURE_DIR.mkdir(exist_ok=True)
    path = FIGURE_DIR / name
    figure.savefig(path)
    plt.close(figure)
    print(f"wrote {path.relative_to(ROOT)}")
    return path


def print_stats() -> None:
    print(f"{'case':<22}{'L max':>12}{'L rms':>11}{'R max':>12}{'R rms':>11}")
    for name, title, gains, model in CASES.values():
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))
        error_left = measured[:, 0] - left
        error_right = measured[:, 1] - right
        print(
            f"{name:<24}"
            f"{np.abs(error_left).max():>12.2e}{np.sqrt(np.mean(error_left**2)):>11.2e}"
            f"{np.abs(error_right).max():>12.2e}{np.sqrt(np.mean(error_right**2)):>11.2e}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the report figures")
    parser.add_argument("--stats", action="store_true", help="also print the residuals")
    args = parser.parse_args()

    if args.stats:
        print_stats()
    figure_law()
    figure_combinations()
    figure_peak()
    figure_residual()
    figure_spectrum()


if __name__ == "__main__":
    main()
