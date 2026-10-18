import wave
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "Source Han Sans SC"

path = Path("output-wav-files/Mixer Circular Panning.wav")

# 读取音频
with wave.open(path, "rb") as wav_file:
    channels = wav_file.getnchannels()
    if channels != 2:
        raise ValueError(f"只支持立体声，实际 {channels} 声道")
    wav_format = wav_file.getformat()
    if wav_format != wave.WAVE_FORMAT_IEEE_FLOAT:
        raise ValueError(f"只支持 32-bit float WAV，实际 {wav_format}")

    sample_rate = wav_file.getframerate()
    n_frames = wav_file.getnframes()
    raw = wav_file.readframes(n_frames)
samples = np.frombuffer(raw, dtype="<f4").reshape(-1, channels)

# 提取实测值
pans = np.arange(n_frames) / n_frames * 2 - 1  # -1 到 1
l2l_measured = samples[:, 0]
l2r_measured = samples[:, 1]

r2l_measured = l2r_measured[::-1]
r2r_measured = l2l_measured[::-1]

after_l_measured = l2l_measured + r2l_measured
after_r_measured = l2r_measured + r2r_measured
P_measured = after_l_measured**2 + after_r_measured**2  # 功率

# ---- 理论值（规则见 README）----
theta = (pans + 1) * np.pi / 4  # 极左 0，中心 pi/4，极右 pi/2
A = np.sqrt(2) * np.cos(theta)
B = np.sqrt(2) * np.sin(theta)

left = pans <= 0  # p <= 0 向左，p >= 0 向右

# 矩阵 M = [[g_ll, g_lr], [g_rl, g_rr]]
l2l_theoretical = np.where(left, A * (1 + B) / 2, A)
l2r_theoretical = np.where(left, 0, B * (1 - A) / 2)
r2l_theoretical = np.where(left, A * (1 - B) / 2, 0)
r2r_theoretical = np.where(left, B, B * (1 + A) / 2)

# L=1, R=0 时的增益极大值：sin(theta) = (sqrt(34) - sqrt(2)) / 8
theta_peak = np.arcsin((np.sqrt(34) - np.sqrt(2)) / 8)
pan_peak = theta_peak * 4 / np.pi - 1
peak_gain = np.sqrt(2) * np.cos(theta_peak) * (1 + np.sqrt(2) * np.sin(theta_peak)) / 2
assert np.isclose(peak_gain, np.sqrt(142 + 34 * np.sqrt(17)) / 16)


# plt.plot(pans, l2l_measured, label="左声道到左声道（实测）")
# plt.plot(pans, l2r_measured, label="左声道到右声道（实测）")
# plt.plot(pans, r2l_measured, label="右声道到左声道（实测）")
# plt.plot(pans, r2r_measured, label="右声道到右声道（实测）")
# plt.plot(pans, after_l_measured, label="总左声道（实测）")
# plt.plot(pans, after_r_measured, label="总右声道（实测）")

# 理论曲线：虚线叠加，应与实测重合
# plt.plot(pans, l2l_theoretical, "k--", lw=1, label="左声道到左声道（理论）")
# plt.plot(pans, l2r_theoretical, "k--", lw=1, label="左声道到右声道（理论）")
# plt.plot(pans, r2l_theoretical, "k--", lw=1, label="右声道到左声道（理论）")
# plt.plot(pans, r2r_theoretical, "k--", lw=1, label="右声道到右声道（理论）")

plt.plot(pans, l2l_measured - l2l_theoretical, label="左声道到左声道（误差）")
plt.plot(pans, l2r_measured - l2r_theoretical, label="左声道到右声道（误差）")

plt.xlabel("pan")
plt.ylabel("value")
plt.minorticks_on()
plt.grid(which="both")
plt.legend()
plt.show()
