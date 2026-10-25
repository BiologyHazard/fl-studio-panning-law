"""Report Figure 11: all-sample residual envelopes and full-sample time detail."""

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
        # Every sample contributes to one min/max bin. No hidden stride sampling.
        bins = np.array_split(np.arange(len(p)), 800)
        centers = np.array([p[b].mean() for b in bins])
        for ch, label in enumerate(("Left", "Right")):
            lo = np.array([e[b, ch].min() for b in bins])
            hi = np.array([e[b, ch].max() for b in bins])
            axes[row, 0].fill_between(centers, lo, hi, color=COLORS[ch], alpha=0.45)
            axes[row, 0].plot(
                centers, (lo + hi) / 2, color=COLORS[ch], lw=0.65, label=label
            )
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
            axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useOffset=False)
            axis.tick_params(axis="y", labelleft=True)
        axes[row, 0].set_xlim(-1, 1)
        axes[row, 1].set_xlim(len(data) / fs - 0.1, len(data) / fs)
    axes[0, 0].set_title("Full sweep: min/max envelopes in 800 bins")
    axes[0, 1].set_title("Last 100 ms: every sample")
    axes[-1, 0].set_xlabel("Nominal pan $p$")
    axes[-1, 1].set_xlabel("Time (s)")
    axes[0, 1].legend(ncols=2)
    save(fig, "03-residual")


if __name__ == "__main__":
    main()
