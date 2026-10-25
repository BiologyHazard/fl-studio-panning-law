"""Compatibility entry point for the rewritten report figures.

The implementation lives in research/; each figure has its own source file.
Statistics are always regenerated. --stats remains accepted for old commands.
"""
import argparse
import runpy
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats", action="store_true", help="accepted for compatibility; statistics are always generated")
    parser.parse_args()
    directory = Path(__file__).resolve().parent / "research"
    sys.path.insert(0, str(directory))
    runpy.run_path(str(directory / "build.py"), run_name="__main__")


if __name__ == "__main__":
    main()
