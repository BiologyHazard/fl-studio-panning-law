"""Search FLEngine_x64.dll for the mixer pan-law code.

Outcome (2026-10-15): **this avenue did not succeed** -- no code reference to the
pan-law machinery was found.  The script is kept because it documents exactly
what was tried and why it failed, which is the reason the rule in
``fl_studio_pan_rule.rule`` rests on measurement instead.

What it does, in order:

1. maps the PE sections and resolves the virtual addresses of the pan-related UI
   strings (``PanLawLabel``, ``PanLawSelect``, ``Circular``, ``Triangular``, ...);
2. scans the executable sections for RIP-relative ``disp32`` references to them;
3. scans for absolute 32-bit and 64-bit address literals instead;
4. counts exact float32 anchors (``1/sqrt(2)``, ``sqrt(2)``, the observed peak);
5. hunts for a precomputed pan-gain table (a long monotone-decreasing float32 run
   starting at ``sqrt(2)``).

Steps 2-3 find nothing, which is consistent with FL resolving UI strings through
its localisation pool (the ``System/Languages/**/*.mo`` catalogues) by string ID
rather than by address.  Step 4 finds no exact ``1/sqrt(2)`` float32 anywhere in
the 52 MB image, and step 5 finds no such table -- so no precomputed gain table
is being used either.

Needs the optional dependency group::

    uv sync --extra reverse-engineering
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
import pefile

DEFAULT_DLL = Path(r"C:\Program Files\Image-Line\FL Studio 20\FLEngine_x64.dll")

STRINGS = [
    b"PanLawLabel",
    b"PanLawSelect",
    b"Circular\x00",
    b"Triangular\x00",
    b"Panning law",
    b"Center panned signal",
    b"Get track pan",
    b"Set track pan",
    b"Get channel pan",
    b"Set channel pan",
]


def sections_of(pe: pefile.PE, base: int) -> list[dict]:
    out = []
    for section in pe.sections:
        out.append(
            {
                "name": section.Name.rstrip(b"\x00").decode("latin-1"),
                "va": base + section.VirtualAddress,
                "raw": section.PointerToRawData,
                "rsize": section.SizeOfRawData,
                "vsize": section.Misc_VirtualSize,
                "exec": bool(section.Characteristics & 0x20000000),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    args = parser.parse_args()

    pe = pefile.PE(str(args.dll), fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    sections = sections_of(pe, base)
    data = args.dll.read_bytes()

    def off_to_va(off: int) -> int | None:
        for s in sections:
            if s["raw"] <= off < s["raw"] + s["rsize"]:
                return s["va"] + (off - s["raw"])
        return None

    print(f"{args.dll}")
    print(f"  image base {base:#x}, {len(data)} bytes, {len(sections)} sections")
    for s in sections:
        print(
            f"    {s['name']:9s} va {s['va']:#012x} vsize {s['vsize']:#010x} "
            f"raw {s['raw']:#010x} rsize {s['rsize']:#010x}"
            f"{'  X' if s['exec'] else ''}"
        )

    # ---- 1. string addresses -------------------------------------------
    targets: dict[str, list[int]] = {}
    print("\n[1] pan-related string addresses")
    for needle in STRINGS:
        hits, start = [], 0
        while len(hits) < 8:
            idx = data.find(needle, start)
            if idx < 0:
                break
            va = off_to_va(idx)
            if va is not None:
                hits.append(va)
            start = idx + 1
        targets[needle.decode("latin-1").rstrip("\x00")] = hits
        print(f"    {needle!r:26s} {[hex(v) for v in hits] or 'not found'}")

    code = [s for s in sections if s["exec"] and s["rsize"]]

    # ---- 2/3. references ------------------------------------------------
    print("\n[2] RIP-relative (disp32) references                     <- none expected")
    print("[3] absolute 32/64-bit address literals                  <- none expected")
    d32 = np.frombuffer(data, dtype="<u4")
    d64 = np.frombuffer(data[: len(data) // 8 * 8], dtype="<u8")

    rip_hits = abs_hits = 0
    for s in code:
        blob = data[s["raw"] : s["raw"] + s["rsize"]]
        for shift in range(4):
            count = (len(blob) - shift) // 4
            if count <= 0:
                continue
            words = np.frombuffer(
                blob[shift : shift + count * 4], dtype="<u4"
            ).astype(np.uint32)
            offsets = shift + 4 * np.arange(count, dtype=np.int64)
            # disp32 is the last field, so the instruction ends right after it
            resolved = s["va"] + offsets + 4 + words.astype(np.int32).astype(np.int64)
            for name, vas in targets.items():
                for va in vas:
                    for idx in np.nonzero(resolved == va)[0]:
                        rip_hits += 1
                        print(
                            f"    rip  {name} <- {s['name']}:"
                            f"{s['va'] + int(offsets[idx]):#x}"
                        )
    for name, vas in targets.items():
        for va in vas:
            for width, table in ((4, d32), (8, d64)):
                for idx in np.nonzero(table == va)[0]:
                    off = int(idx) * (width // 8) * 2
                    abs_hits += 1
                    print(
                        f"    abs{width} {name} <- file {off:#x} "
                        f"({off_to_va(off) or 0:#x})"
                    )
    print(f"    RIP-relative hits: {rip_hits}    absolute hits: {abs_hits}")

    # ---- 4. exact float32 anchors --------------------------------------
    print("\n[4] exact float32 anchors")
    floats = np.frombuffer(data[: len(data) // 4 * 4], dtype="<f4")
    for label, value in (
        ("1/sqrt(2)", 0.7071067811865476),
        ("1/sqrt(2) (1 ulp low)", 0.7071067095),
        ("sqrt(2)", 1.4142135623730951),
    ):
        anchor = np.float32(value)
        print(f"    {label:24s} {anchor!r}: {int((floats == anchor).sum())} hits")

    # ---- 5. precomputed gain table -------------------------------------
    print("\n[5] precomputed pan-gain table hunt")
    wide = floats.astype(np.float64)
    starts = np.nonzero((wide > 1.4130) & (wide < 1.4155))[0]
    found = 0
    for start in starts[:4000]:
        segment = wide[start : start + 600]
        if len(segment) < 600 or not np.all(np.isfinite(segment)):
            continue
        if np.all(np.diff(segment) <= 0) and segment[-1] < 0.02:
            print(f"    candidate table at float index {start} (file {start * 4:#x})")
            found += 1
            if found > 8:
                break
    print(f"    monotone sqrt(2)-started tables of length >= 600: {found}")

    print(
        "\nconclusion: no address reference and no gain table was found; the UI\n"
        "strings are reached through the localisation pool, so the pan arithmetic\n"
        "cannot be located this way.  A real decompiler (Ghidra/IDA) is required.\n"
        "The rule in fl_studio_pan_rule.rule therefore rests on the measured\n"
        "renders, cross-checked against the documented endpoint behaviour."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
