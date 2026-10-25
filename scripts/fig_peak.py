"""Report Figure 15: Mixer Circular interior amplitude maximum."""

import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, matrix, save, style


def main():
    style()
    fig, axis = plt.subplots(figsize=(7, 4))
    q = np.linspace(-1, 0, 2001)
    f = matrix(q, CASES[0])[..., 0, 0]
    theta = np.arcsin((np.sqrt(34) - np.sqrt(2)) / 8)
    qpeak = 4 * theta / np.pi - 1
    peak = np.sqrt(142 + 34 * np.sqrt(17)) / 16
    axis.plot(q, f, color=COLORS[0])
    axis.axhline(1, color=".45", lw=0.8, ls=":")
    axis.plot(qpeak, peak, "o", color=COLORS[1])
    axis.annotate(
        rf"$p = {qpeak:.6f}$"
        "\n"
        rf"$\text{{gain}} = {peak:.7f}$"
        "\n"
        rf"$+{20 * np.log10(peak):.4f}\,\text{{dB}}$",
        xy=(qpeak, peak),
        xytext=(-0.95, 1.085),
        va="top",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": ".4"},
    )
    axis.set(
        title="Mixer Circular: interior maximum",
        xlabel="Pan $p$",
        ylabel=r"Left output for input $(1, 0)^\top$",
        xlim=(-1, 0),
        ylim=(0.68, 1.12),
    )
    save(fig, "06-peak")


if __name__ == "__main__":
    main()
