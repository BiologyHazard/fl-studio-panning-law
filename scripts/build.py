"""Regenerate report evidence; paths are independent of the working directory."""

import analyze
import fig_consequences
import fig_identity
import fig_matrix
import fig_residual
import fig_response


def main():
    analyze.main()
    for module in (
        fig_response,
        fig_matrix,
        fig_residual,
        fig_identity,
        fig_consequences,
    ):
        module.main()


if __name__ == "__main__":
    main()
