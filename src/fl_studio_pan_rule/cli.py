"""Command line entry point for ``fl-studio-pan-rule``."""

from __future__ import annotations

import argparse
import sys

from . import analysis, rule

__all__ = ["main"]

TABLE_PANS = (-1.0, -0.75, -0.519251, -0.5, -0.255318, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0)


def _table(points) -> None:
    header = (
        f"  {'pan':>7}  {'theta':>8}  {'A':>8}  {'B':>8} |"
        f" {'gLL':>9} {'gLR':>9} {'gRL':>9} {'gRR':>9}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for pan in points:
        theta = float(rule.theta(pan))
        a, b = (float(v) for v in rule.circular_gains(pan))
        g_ll, g_lr, g_rl, g_rr = (float(v) for v in rule.gains(pan))
        print(
            f"  {pan:+7.4f}  {theta:8.6f}  {a:+8.6f}  {b:+8.6f} |"
            f" {g_ll:+9.6f} {g_lr:+9.6f} {g_rl:+9.6f} {g_rr:+9.6f}"
        )
    print()
    print("  theta = (pan + 1) * pi/4,  A = sqrt(2)cos(theta),  B = sqrt(2)sin(theta)")
    print("  pan <= 0 :  L' = A*((1+B)/2*L + (1-B)/2*R),  R' = B*R")
    print("  pan >= 0 :  L' = A*L,  R' = B*((1+A)/2*R + (1-A)/2*L)")


def _eval(pan: float, left: float, right: float) -> None:
    out_left, out_right = rule.process(pan, left, right)
    print(f"pan   = {pan:+.9f}   theta = {float(rule.theta(pan)):.9f}")
    print(f"input = ({left:+.6f}, {right:+.6f})")
    print(f"out   = ({float(out_left):+.9f}, {float(out_right):+.9f})")
    m = rule.matrix(pan)
    print("matrix:")
    for row in m:
        print("   [" + ", ".join(f"{float(v):+.9f}" for v in row) + "]")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fl-studio-pan-rule",
        description="FL Studio mixer-track pan rule for stereo signals "
        "(reverse-engineered). 'verify' re-runs every check against "
        "the bundled renders.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("verify", help="re-run all verification checks (default)")
    sub.add_parser("table", help="print the gain table")
    ev = sub.add_parser("eval", help="evaluate one pan position")
    ev.add_argument("pan", type=float)
    ev.add_argument("--left", type=float, default=1.0)
    ev.add_argument("--right", type=float, default=0.0)

    args = parser.parse_args(argv)

    if args.command == "table":
        _table(TABLE_PANS)
        return 0
    if args.command == "eval":
        _eval(args.pan, args.left, args.right)
        return 0

    try:
        results = analysis.verify_all()
    except FileNotFoundError as exc:
        print(f"cannot locate the render data: {exc}", file=sys.stderr)
        return 2
    print(analysis.format_report(results))

    fit = results["rule_fit"]["timelines"]["theta_from_render"]
    ok = fit["L_max_rel"] < 1e-5 and results["mono_power"]["relative_spread"] < 1e-2
    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
