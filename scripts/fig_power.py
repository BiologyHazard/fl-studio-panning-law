"""Report Figure 14: model power relationships for two input conditions."""

import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, gains, matrix, save, style


def main():
    style()
    p = np.linspace(-1, 1, 4001)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for law, color in zip(("Circular", "Triangular"), COLORS, strict=True):
        u, v = gains(p, law)
        axes[0].plot(p, (u * u + v * v) / 2, color=color, label=law)
    axes[0].set(
        title=r"(a) Duplicated mono: input $(s, s)^\top$",
        xlabel="Pan $p$",
        ylabel="Output / input sum of squares",
        ylim=(0.45, 1.08),
    )
    axes[0].legend()
    for case, color, ls in zip(
        CASES,
        (COLORS[0], COLORS[0], COLORS[1], COLORS[1]),
        ("-", "--", "-", "--"),
        strict=True,
    ):
        a = matrix(p, case)
        axes[1].plot(
            p, np.sum(a[..., :, 0] ** 2, axis=1), color=color, ls=ls, label=case.name
        )
    axes[1].set(
        title=r"(b) Left-only input: $(1, 0)^\top$",
        xlabel="Pan $p$",
        ylabel="Output sum of squares",
    )
    axes[1].legend(fontsize=8)
    save(fig, "05-power")


if __name__ == "__main__":
    main()
