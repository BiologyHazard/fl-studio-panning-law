"""把 FL Studio 的 Pan 拆成「Pan law × 实现」四种组合，与渲染结果逐一对照。

数据来自 ``output-wav-files/``：输入恒为 ``L = 1, R = 0``，pan 在 8 s 内从 -100% 线性扫到 +100%。

Pan law 只决定单声道增益 ``(gL, gR)``：

    Circular    gL = √2·cos θ,  gR = √2·sin θ      θ = (p + 1)·π/4
    Triangular  gL = 1 − max(p, 0),  gR = 1 + min(p, 0)

实现决定立体声如何混合：

    Mixer        p ≤ 0:  L' = gL·[(1+gR)/2·L + (1−gR)/2·R],  R' = gR·R
                 p ≥ 0:  L' = gL·L,  R' = gR·[(1+gL)/2·R + (1−gL)/2·L]
    Audio Clip   L' = gL·L,  R' = gR·R            （纯 balance，不交叉混合）

两者对单声道输入完全相同（``(L', R') = s·(gL, gR)``），差别只在立体声的交叉混合。
"""

import wave
from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "Source Han Sans SC"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output-wav-files"

Gains = Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]]
Implementation = Callable[
    [np.ndarray, np.ndarray, np.ndarray, tuple[np.ndarray, np.ndarray]],
    tuple[np.ndarray, np.ndarray],
]


def load_render(name: str) -> np.ndarray:
    path = OUTPUT_DIR / f"{name} Panning.wav"
    with wave.open(path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        if channels != 2:
            raise ValueError(f"只支持立体声，实际 {channels} 声道")
        wav_format = wav_file.getformat()
        if wav_format != wave.WAVE_FORMAT_IEEE_FLOAT:
            raise ValueError(f"只支持 32-bit float WAV，实际 {wav_format}")
        n_frames = wav_file.getnframes()
        raw = wav_file.readframes(n_frames)
    return np.frombuffer(raw, dtype="<f4").reshape(-1, channels)


def circular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta = (pan + 1) * np.pi / 4
    return np.sqrt(2) * np.cos(theta), np.sqrt(2) * np.sin(theta)


def triangular_gains(pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return 1 - np.maximum(pan, 0), 1 + np.minimum(pan, 0)


def through_mixer(
    pan: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    gains: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """混音台轨道 Pan：远端声道按 (1 − g远端)/2 的权重混入近端，100% 时折叠成单声道和。"""
    g_left, g_right = gains
    to_left = pan <= 0

    out_left = np.where(
        to_left,
        g_left * ((1 + g_right) / 2 * left + (1 - g_right) / 2 * right),
        g_left * left,
    )
    out_right = np.where(
        to_left,
        g_right * right,
        g_right * ((1 + g_left) / 2 * right + (1 - g_left) / 2 * left),
    )
    return out_left, out_right


def through_channel(
    pan: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    gains: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """通道（Audio Clip / Sampler）Pan：左右各自乘增益，纯 balance，不做交叉混合。"""
    g_left, g_right = gains
    return g_left * left, g_right * right


CASES: list[tuple[str, str, Gains, Implementation]] = [
    ("Mixer Circular", "Mixer Circular", circular_gains, through_mixer),
    ("Mixer Triangular", "Mixer Triangular", triangular_gains, through_mixer),
    ("Audio Clip Circular", "Audio Clip Circular", circular_gains, through_channel),
    (
        "Audio Clip Triangular",
        "Audio Clip Triangular",
        triangular_gains,
        through_channel,
    ),
]


def main() -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    print(f"{'组合':<22}{'L 误差 max':>12}{'L rms':>11}{'R 误差 max':>12}{'R rms':>11}")

    for axis, (title, name, gains, implementation) in zip(axes.flat, CASES):
        measured = load_render(name)
        n_frames = len(measured)
        pans = np.arange(n_frames) / (n_frames - 1) * 2 - 1

        left = np.ones(n_frames)
        right = np.zeros(n_frames)
        model_left, model_right = implementation(pans, left, right, gains(pans))

        error_left = measured[:, 0] - model_left
        error_right = measured[:, 1] - model_right
        print(
            f"{title:<22}{np.abs(error_left).max():>12.2e}{np.sqrt(np.mean(error_left**2)):>11.2e}"
            f"{np.abs(error_right).max():>12.2e}{np.sqrt(np.mean(error_right**2)):>11.2e}"
        )

        axis.plot(pans, measured[:, 0], label="左输出（实测）")
        axis.plot(pans, measured[:, 1], label="右输出（实测）")
        axis.plot(pans, model_left, "k--", lw=1, label="左输出（模型）")
        axis.plot(pans, model_right, "k--", lw=1, label="右输出（模型）")
        axis.set_title(title)
        axis.minorticks_on()
        axis.grid(which="both")

    figure.supxlabel("pan")
    figure.supylabel("增益")
    axes[0, 0].legend()
    plt.show()


if __name__ == "__main__":
    main()
