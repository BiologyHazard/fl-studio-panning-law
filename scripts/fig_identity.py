"""Report Figure 13: cross-output tests independent of the nominal pan ramp."""

import matplotlib.pyplot as plt
import numpy as np
from analyze import identity_residual
from common import CASES, COLORS, measured, save, style


def main():
    style()
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7))
    for row, case in enumerate(CASES[:2]):
        p, data = measured(case)
        selected = data[p > 0]
        x = np.linspace(0, 1, 2001)
        y = (1 - x) / 2
        if case.law == "Circular":
            y *= np.sqrt(2 - x**2)
        axes[row, 0].plot(x, y, color=COLORS[0], label="Model relation")
        ix = np.linspace(0, len(selected) - 1, 61, dtype=int)
        axes[row, 0].plot(
            selected[ix, 0],
            selected[ix, 1],
            "o",
            ms=3,
            mfc="white",
            mec=COLORS[1],
            label="Measured pairs",
        )
        _, e = identity_residual(case)
        axes[row, 1].hist(e, bins=80, color=COLORS[0], alpha=0.8)
        axes[row, 0].set(
            title=case.name, xlabel="Measured left output", ylabel="Right output"
        )
        axes[row, 1].set(
            title="All positive-pan samples",
            xlabel="Relation residual",
            ylabel="Sample count",
        )
        axes[row, 1].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        axes[row, 1].ticklabel_format(axis="x", style="sci", scilimits=(0, 0), useOffset=False)
    axes[0, 0].legend()
    save(fig, "04-identity")


if __name__ == "__main__":
    main()
