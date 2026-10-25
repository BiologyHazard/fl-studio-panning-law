"""Regenerate report evidence; paths are independent of the working directory."""

import analyze
import fig_identity
import fig_matrix
import fig_peak
import fig_power
import fig_residual
import fig_response


def main():
    analyze.main()
    for module in (
        fig_response,
        fig_matrix,
        fig_residual,
        fig_identity,
        fig_power,
        fig_peak,
    ):
        module.main()


if __name__ == "__main__":
    main()
