"""Report Figure 11: full matrix, distinguishing symmetry-derived entries."""

import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, matrix, save, style


def main():
    style()
    p = np.linspace(-1, 1, 2001)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
    for ax, case, letter in zip(axes.flat, CASES, "abcd", strict=True):
        a = matrix(p, case)
        for row, col, color, ls in [
            (0, 0, COLORS[0], "-"),
            (1, 0, COLORS[1], "-"),
            (1, 1, COLORS[0], "--"),
            (0, 1, COLORS[1], "--"),
        ]:
            origin = "first-column model" if col == 0 else "symmetry-derived"
            ax.plot(
                p,
                a[:, row, col],
                color=color,
                ls=ls,
                lw=1.7,
                label=f"$A_{{{row + 1}{col + 1}}}$: {origin}",
            )
        ax.set(title=f"({letter}) {case.name}", xlim=(-1, 1), ylim=(-0.06, 1.5))
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    for ax in axes[-1]:
        ax.set_xlabel("Pan $p$")
    for ax in axes[:, 0]:
        ax.set_ylabel("Matrix coefficient (model)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2)
    save(fig, "02-matrix")


if __name__ == "__main__":
    main()
