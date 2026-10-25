"""Report Figure 10: directly observed first column against the model."""

import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, matrix, measured, save, style


def main():
    style()
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
    for ax, case, letter in zip(axes.flat, CASES, "abcd", strict=True):
        p, data = measured(case)
        model_p = np.linspace(-1, 1, 2001)
        model = matrix(model_p, case)[..., :, 0]
        samples = np.linspace(0, len(p) - 1, 61, dtype=int)
        for ch, label, marker in zip(
            range(2), ("Left", "Right"), ("o", "s"), strict=True
        ):
            ax.plot(
                model_p, model[:, ch], color=COLORS[ch], lw=1.7, label=f"{label}: model"
            )
            ax.plot(
                p[samples],
                data[samples, ch],
                linestyle="none",
                marker=marker,
                ms=3.5,
                mfc="white",
                mec=COLORS[ch],
                label=f"{label}: measured",
            )
        ax.set(title=f"({letter}) {case.name}", xlim=(-1.03, 1.03), ylim=(-0.07, 1.52))
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    for ax in axes[-1]:
        ax.set_xlabel("Nominal pan $p$")
    for ax in axes[:, 0]:
        ax.set_ylabel("Output amplitude for input (1, 0)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=4)
    save(fig, "01-response")


if __name__ == "__main__":
    main()
