"""Figure 5: conditional model predictions, not additional experiments."""
import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, gains, matrix, save, style


def main():
    style()
    p = np.linspace(-1, 1, 4001)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for law, color in zip(("Circular", "Triangular"), COLORS):
        u, v = gains(p, law)
        axes[0].plot(p, (u*u + v*v) / 2, color=color, label=law)
    axes[0].set(title="(a) Duplicated mono: input (s, s)",
                xlabel="Pan $p$", ylabel="Output / input sum of squares", ylim=(.45, 1.08))
    axes[0].legend()
    for case, color, ls in zip(CASES, (COLORS[0], COLORS[0], COLORS[1], COLORS[1]),
                               ("-", "--", "-", "--")):
        a = matrix(p, case)
        axes[1].plot(p, np.sum(a[..., :, 0] ** 2, axis=1), color=color, ls=ls, label=case.name)
    axes[1].set(title="(b) Left-only input: (1, 0)", xlabel="Pan $p$",
                ylabel="Output sum of squares")
    axes[1].legend(fontsize=8)
    q = np.linspace(-1, 0, 2001)
    f = matrix(q, CASES[0])[..., 0, 0]
    theta = np.arcsin((np.sqrt(34) - np.sqrt(2)) / 8)
    qpeak = 4 * theta / np.pi - 1
    peak = np.sqrt(142 + 34 * np.sqrt(17)) / 16
    axes[2].plot(q, f, color=COLORS[0])
    axes[2].axhline(1, color=".45", lw=.8, ls=":")
    axes[2].plot(qpeak, peak, "o", color=COLORS[1])
    axes[2].annotate(f"p = {qpeak:.6f}\ngain = {peak:.7f}\n+{20*np.log10(peak):.4f} dB",
                     xy=(qpeak, peak), xytext=(-.95, 1.085), va="top", fontsize=9,
                     arrowprops={"arrowstyle": "->", "color": ".4"})
    axes[2].set(title="(c) Mixer Circular: interior maximum", xlabel="Pan $p$",
                ylabel="Left output for input (1, 0)", xlim=(-1, 0), ylim=(.68, 1.12))
    save(fig, "05-consequences")


if __name__ == "__main__":
    main()
