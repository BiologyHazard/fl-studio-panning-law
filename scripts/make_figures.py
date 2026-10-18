"""生成报告（README）中的全部插图，并打印四种组合的逐帧残差。

用法::

    uv run python scripts/make_figures.py            # 只生成图片
    uv run python scripts/make_figures.py --stats    # 同时打印残差统计

数据来自 ``output-wav-files/``：输入恒为 ``L = 1, R = 0``，pan 在 8 秒内从 -100% 线性扫到 +100%。

Pan law 只决定单声道增益 ``(gL, gR)``：

    Circular    gL = sqrt(2)*cos(theta),  gR = sqrt(2)*sin(theta),  theta = (p+1)*pi/4
    Triangular  gL = 1 - max(p, 0),       gR = 1 + min(p, 0)

实现决定立体声如何混合：

    Mixer        p <= 0: L' = gL*[(1+gR)/2*L + (1-gR)/2*R],  R' = gR*R
                 p >= 0: L' = gL*L,                          R' = gR*[(1+gL)/2*R + (1-gL)/2*L]
    Channel      L' = gL*L,  R' = gR*R    (纯 balance，不交叉混合)
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
        "font.family": "Source Han Sans SC",
        "axes.unicode_minus": False,
        "figure.dpi": 110,
        "savefig.dpi": 220,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "figure.constrained_layout.use": True,
    }
)

Gains = Callable[[np.ndarray], "tuple[np.ndarray, np.ndarray]"]
Model = Callable[
    [np.ndarray, "tuple[np.ndarray, np.ndarray]"], "tuple[np.ndarray, np.ndarray]"
]

COLOR_LEFT = "#c0392b"
COLOR_RIGHT = "#1f6fb4"
COLOR_MODEL = "#333333"


# --------------------------------------------------------------------------- 数据


def load_render(name: str) -> np.ndarray:
    """读取 32-bit float 立体声 WAV，返回 (n, 2) 的 float64 数组。"""
    path = OUTPUT_DIR / f"{name} Panning.wav"
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getnchannels() != 2:
            raise ValueError(f"只支持立体声：{path}")
        if wav_file.getformat() != wave.WAVE_FORMAT_IEEE_FLOAT:
            raise ValueError(f"只支持 32-bit float WAV：{path}")
        raw = wav_file.readframes(wav_file.getnframes())
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)


def pan_grid(n_frames: int) -> np.ndarray:
    return np.arange(n_frames) / (n_frames - 1) * 2 - 1


# --------------------------------------------------------------------------- 模型


def circular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta = (pan + 1) * np.pi / 4
    return np.sqrt(2) * np.cos(theta), np.sqrt(2) * np.sin(theta)


def triangular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return 1 - np.maximum(pan, 0), 1 + np.minimum(pan, 0)


def mixer(
    pan: np.ndarray, gains: tuple[np.ndarray, np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """混音台轨道 Pan：远端声道按 (1 - g远端)/2 的权重混入近端。"""
    g_left, g_right = gains
    to_left = pan <= 0
    left = np.where(to_left, g_left * (1 + g_right) / 2, g_left)
    right = np.where(to_left, 0.0, g_right * (1 - g_left) / 2)
    return left, right


def channel(
    pan: np.ndarray, gains: tuple[np.ndarray, np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """通道 Pan：纯 balance。输入 L=1, R=0，故只有左输出非零。"""
    g_left, _ = gains
    return g_left, np.zeros_like(g_left)


CASES = {
    "mixer-circular": (
        "Mixer Circular",
        "混音台轨道 × Circular",
        circular_gains,
        mixer,
    ),
    "mixer-triangular": (
        "Mixer Triangular",
        "混音台轨道 × Triangular",
        triangular_gains,
        mixer,
    ),
    "channel-circular": (
        "Audio Clip Circular",
        "通道 × Circular",
        circular_gains,
        channel,
    ),
    "channel-triangular": (
        "Audio Clip Triangular",
        "通道 × Triangular",
        triangular_gains,
        channel,
    ),
}


# --------------------------------------------------------------------------- 图 1


def figure_combinations() -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for axis, case in zip(axes.flat, CASES.values()):
        name, title, gains, model = case
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))

        axis.plot(pan, measured[:, 0], color=COLOR_LEFT, lw=1.2, label="左输出（实测）")
        axis.plot(
            pan, measured[:, 1], color=COLOR_RIGHT, lw=1.2, label="右输出（实测）"
        )
        axis.plot(
            pan, left, color="0.72", lw=4.0, zorder=0, label="模型（左右两根粗线）"
        )
        axis.plot(pan, right, color="0.72", lw=4.0, zorder=0)
        axis.axhline(1.0, color="0.45", lw=0.8, ls=":", zorder=0)
        axis.set_title(title, fontsize=11)
        axis.set_xlim(-1, 1)
        axis.set_ylim(-0.02, 1.5)
        axis.xaxis.set_major_locator(MultipleLocator(0.5))

    for axis in axes[1]:
        axis.set_xlabel("pan")
    for axis in axes[:, 0]:
        axis.set_ylabel("输出（输入 L=1, R=0）")
    axes[0, 0].legend(loc="upper right", fontsize=9)
    return save(figure, "fig02-combinations.png")


# --------------------------------------------------------------------------- 图 2


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
    gain_axis.set(xlabel="pan", ylabel="单声道增益", title="两种 Pan law 的单声道增益")
    gain_axis.xaxis.set_major_locator(MultipleLocator(0.5))
    gain_axis.legend(fontsize=9, ncols=2)

    shape_axis.plot(circ_left, circ_right, color="#2f7d32", lw=2.0, label="Circular")
    shape_axis.plot(tri_left, tri_right, color="#a0522d", lw=2.0, label="Triangular")
    shape_axis.set(
        xlabel="$g_L$",
        ylabel="$g_R$",
        title="声像轨迹：$(g_L, g_R)$ 随 pan 的走向",
        aspect="equal",
        xlim=(-0.05, 1.6),
        ylim=(-0.05, 1.6),
    )
    shape_axis.legend(loc="upper right")
    for label, p in [("极左", -1), ("中心", 0), ("极右", 1)]:
        theta = (p + 1) * np.pi / 4
        shape_axis.plot(
            [np.sqrt(2) * np.cos(theta)],
            [np.sqrt(2) * np.sin(theta)],
            "o",
            color="#2f7d32",
            ms=5,
        )
        shape_axis.annotate(
            label,
            (np.sqrt(2) * np.cos(theta), np.sqrt(2) * np.sin(theta)),
            textcoords="offset points",
            xytext=(6, -12),
            fontsize=9,
        )
    return save(figure, "fig01-law.png")


# --------------------------------------------------------------------------- 图 3


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
    axis.plot(pan, gain, color="#c0392b", lw=2.0, label="$L'$（$L=1,\\ R=0$，模型）")
    axis.axhline(1.0, color="0.4", lw=0.9, ls="-")
    axis.fill_between(pan, 1.0, gain, where=gain > 1.0, color="#c0392b", alpha=0.15)
    axis.plot([peak_pan], [peak_gain], "o", color="#c0392b", ms=6)
    axis.annotate(
        f"峰值 {peak_gain:.7f}\n$p={peak_pan:.6f}$（$+0.4229$ dB）\n"
        f"$L'>1$ 区间 $p\\in[{crossing:.4f},0]$",
        (peak_pan, peak_gain),
        textcoords="offset points",
        xytext=(18, -18),
        ha="left",
        va="top",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "0.35"},
    )
    axis.set(
        xlabel="pan",
        ylabel="$L'$",
        title="Mixer × Circular 的中间突起（唯一超过 0 dB 的组合）",
        xlim=(-1, 0),
        ylim=(0.68, 1.075),
    )
    axis.legend(loc="upper left")
    return save(figure, "fig03-peak.png")


# --------------------------------------------------------------------------- 图 4


def figure_residual() -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(11, 6), sharex=True)
    for axis, case in zip(axes.flat, CASES.values()):
        name, title, gains, model = case
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))

        residual_left = measured[:, 0] - left
        residual_right = measured[:, 1] - right
        axis.plot(pan, residual_left * 1e6, color=COLOR_LEFT, lw=0.9, label="$L'$ 残差")
        if np.any(residual_right):
            axis.plot(
                pan, residual_right * 1e6, color=COLOR_RIGHT, lw=0.9, label="$R'$ 残差"
            )
        axis.set_title(title, fontsize=11)
        axis.set_xlim(-1, 1)
        axis.xaxis.set_major_locator(MultipleLocator(0.5))

    for axis in axes[1]:
        axis.set_xlabel("pan")
    for axis in axes[:, 0]:
        axis.set_ylabel("实测 − 模型 ($\\times10^{-6}$)")
    axes[0, 0].legend(loc="lower left", fontsize=9)
    return save(figure, "fig04-residual.png")


# --------------------------------------------------------------------------- 图 5


def figure_spectrum() -> Path:
    """把前向残差换算成实际 pan 偏差，暴露自动化时间轴的周期性误差。"""
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
        xlabel="时间 (ms)",
        ylabel="实际 pan − 名义 pan ($\\times10^{-3}$)",
        title="自动化时间轴的误差（前 100 ms）",
        xlim=(0, 100),
    )
    time_axis.axvline(750 / 48, color="0.4", lw=0.8, ls="--")
    time_axis.annotate(
        "15.625 ms",
        (750 / 48, 1.4),
        textcoords="offset points",
        xytext=(4, 0),
        fontsize=9,
    )

    freqs = np.arange(len(spectrum)) * 48000 / n_frames
    freq_axis.semilogy(freqs[5:], spectrum[5:], lw=0.9)
    freq_axis.set(
        xlabel="频率 (Hz)",
        ylabel="幅度（对数）",
        title="误差的主频在 64 Hz（= 48 kHz / 750）",
        xlim=(0, 400),
    )
    freq_axis.axvline(frequency, color="#c0392b", lw=1.0, ls="--")
    freq_axis.annotate(
        f"{frequency:.2f} Hz",
        (frequency, spectrum[index]),
        textcoords="offset points",
        xytext=(6, 2),
        fontsize=9,
    )
    return save(figure, "fig06-spectrum.png")


# --------------------------------------------------------------------------- 图 6


def figure_rejection() -> Path:
    pan = pan_grid(len(load_render("Mixer Circular")))
    reference = {
        "Mixer Circular": (mixer, circular_gains),
        "Mixer Triangular": (mixer, triangular_gains),
        "Audio Clip Circular": (channel, circular_gains),
        "Audio Clip Triangular": (channel, triangular_gains),
    }
    labels: list[str] = []
    values: list[float] = []
    colors: list[str] = []

    for name, (model, gains) in reference.items():
        measured = load_render(name)[:, 0]
        predicted = model(pan, gains(pan))[0]
        labels.append(f"{name}\n（正确模型）")
        values.append(np.sqrt(np.mean((measured - predicted) ** 2)))
        colors.append("#2f7d32")

    wrong = [
        ("Mixer Circular", channel, circular_gains, "balance → Mixer Circ."),
        ("Mixer Triangular", channel, triangular_gains, "balance → Mixer Tri."),
        ("Mixer Circular", mixer, triangular_gains, "Triangular → Mixer Circ."),
        ("Mixer Triangular", mixer, circular_gains, "Circular → Mixer Tri."),
        ("Audio Clip Circular", mixer, circular_gains, "Mixer 式 → Channel Circ."),
        ("Audio Clip Triangular", mixer, triangular_gains, "Mixer 式 → Channel Tri."),
    ]
    for name, model, gains, label in wrong:
        measured = load_render(name)[:, 0]
        predicted = model(pan, gains(pan))[0]
        labels.append(label)
        values.append(np.sqrt(np.mean((measured - predicted) ** 2)))
        colors.append("#c0392b")

    figure, axis = plt.subplots(figsize=(10, 4.2))
    bars = axis.bar(range(len(values)), values, color=colors, width=0.7)
    axis.set_yscale("log")
    axis.set_ylabel("$L'$ 残差 rms（对数）")
    axis.set_xticks(range(len(labels)), labels, fontsize=8, rotation=18, ha="right")
    axis.set_title("正确模型与错误模型的残差对比")
    for bar, value in zip(bars, values):
        axis.annotate(
            f"{value:.1e}",
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 3),
            ha="center",
            fontsize=7.5,
        )
    return save(figure, "fig05-rejection.png")


# --------------------------------------------------------------------------- 工具


def save(figure: plt.Figure, name: str) -> Path:
    FIGURE_DIR.mkdir(exist_ok=True)
    path = FIGURE_DIR / name
    figure.savefig(path)
    plt.close(figure)
    print(f"wrote {path.relative_to(ROOT)}")
    return path


def print_stats() -> None:
    print(f"{'组合':<22}{'L 误差 max':>12}{'L rms':>11}{'R 误差 max':>12}{'R rms':>11}")
    for name, title, gains, model in CASES.values():
        measured = load_render(name)
        pan = pan_grid(len(measured))
        left, right = model(pan, gains(pan))
        error_left = measured[:, 0] - left
        error_right = measured[:, 1] - right
        print(
            f"{title:<22}{np.abs(error_left).max():>12.2e}{np.sqrt(np.mean(error_left**2)):>11.2e}"
            f"{np.abs(error_right).max():>12.2e}{np.sqrt(np.mean(error_right**2)):>11.2e}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="生成报告插图")
    parser.add_argument("--stats", action="store_true", help="同时打印逐帧残差统计")
    args = parser.parse_args()

    if args.stats:
        print_stats()
    figure_combinations()
    figure_law()
    figure_peak()
    figure_residual()
    figure_spectrum()
    figure_rejection()


if __name__ == "__main__":
    main()
