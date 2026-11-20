"""Report Figure 12: per-sample signed residuals and full-sample time detail."""

import matplotlib.pyplot as plt
import numpy as np
from common import CASES, COLORS, matrix, measured, read_wav, save, style


def main():
    style()
    fig, axes = plt.subplots(4, 2, figsize=(11, 10), sharex="col", sharey=True)
    for row, case in enumerate(CASES):
        p, data = measured(case)
        fs, _ = read_wav(case.path)
        e = data - matrix(p, case)[..., :, 0]
        for ch, label in enumerate(("Left", "Right")):
            axes[row, 0].plot(p, e[:, ch], color=COLORS[ch], lw=0.5, label=label)
            count = round(0.1 * fs)
            axes[row, 1].plot(
                np.arange(len(data) - count, len(data)) / fs,
                e[-count:, ch],
                color=COLORS[ch],
                lw=0.8,
                label=label,
            )
        axes[row, 0].set_ylabel(f"{case.name}\nResidual")
        for axis in axes[row]:
            axis.ticklabel_format(
                axis="y", style="sci", scilimits=(0, 0), useOffset=False
            )
            axis.tick_params(axis="y", labelleft=True)
        axes[row, 0].set_xlim(-1, 1)
        axes[row, 1].set_xlim(len(data) / fs - 0.1, len(data) / fs)
    axes[0, 0].set_title("Residual (Full sweep)")
    axes[0, 1].set_title("Residual (Last 100 ms)")
    axes[-1, 0].set_xlabel("Pan $p$")
    axes[-1, 1].set_xlabel("Time (s)")
    axes[0, 1].legend(ncols=2)
    save(fig, "03-residual")


if __name__ == "__main__":
    main()
