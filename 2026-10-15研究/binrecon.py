"""Static recon of FLEngine_x64.dll: locate the pan-law code.

Stage 1: PE section map.
Stage 2: resolve VAs of interesting strings.
Stage 3: scan the code sections for RIP-relative disp32 references to those VAs.
Stage 4: scan for float32 tables whose values match the MEASURED pan curve.
"""

import struct
import sys
from pathlib import Path

import numpy as np
import pefile

DLL = Path(r"C:\Program Files\Image-Line\FL Studio 20\FLEngine_x64.dll")
OUT = Path(__file__).parent

pe = pefile.PE(str(DLL), fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
print(f"ImageBase = {image_base:#x}   Timestamp = {pe.FILE_HEADER.TimeDateStamp:#x}")

sections = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("latin-1")
    va = image_base + s.VirtualAddress
    raw = s.PointerToRawData
    vsize = s.Misc_VirtualSize
    rsize = s.SizeOfRawData
    chars = s.Characteristics
    writable = bool(chars & 0x80000000)
    execable = bool(chars & 0x20000000)
    sections.append(dict(name=name, va=va, raw=raw, vsize=vsize, rsize=rsize,
                         w=writable, x=execable))
    print(f"  {name:9s} VA={va:#012x} vsize={vsize:#010x} raw={raw:#010x} "
          f"rsize={rsize:#010x} {'W' if writable else '-'}{'X' if execable else '-'}")

data = DLL.read_bytes()
print(f"file size = {len(data)}")


def va_to_off(va):
    for s in sections:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            return s["raw"] + (va - s["va"])
    return None


def off_to_va(off):
    for s in sections:
        if s["raw"] <= off < s["raw"] + s["rsize"]:
            return s["va"] + (off - s["raw"])
    return None


# ---------------------------------------------------------------- stage 2
TARGETS = [b"PanLawLabel", b"PanLawSelect", b"Circular\x00", b"Triangular\x00",
           b"Panning law", b"Get track pan", b"Set track pan",
           b"Get channel pan", b"Set channel pan", b"Center panned signal"]

print("\n=== string VAs ===")
found = {}
for t in TARGETS:
    start = 0
    hits = []
    while True:
        i = data.find(t, start)
        if i < 0:
            break
        v = off_to_va(i)
        if v is not None:
            hits.append(v)
        start = i + 1
        if len(hits) > 12:
            break
    found[t] = hits
    print(f"  {t!r:26s} -> " + ", ".join(f"{v:#x}" for v in hits[:12]))

# ---------------------------------------------------------------- stage 3
code = [s for s in sections if s["x"] and s["rsize"]]
print(f"\n=== scanning {sum(s['rsize'] for s in code)} bytes of code for "
      f"RIP-relative refs (disp32) ===")

flat = []
for s in code:
    blob = data[s["raw"]: s["raw"] + s["rsize"]]
    a = np.frombuffer(blob, dtype=np.uint8)
    flat.append((s, a))

allv = set()
for t, vs in found.items():
    allv.update(vs)

for s, a in flat:
    blob = a.tobytes()
    n = len(blob)
    for k in range(4):
        nsub = (n - k) // 4
        if nsub <= 0:
            continue
        arr = np.frombuffer(blob[k: k + nsub * 4], dtype="<u4").astype(np.uint32)
        offs = k + 4 * np.arange(len(arr), dtype=np.int64)
        # instruction containing this disp32 ends at offs+4
        tgt = s["va"] + offs + 4 + arr.astype(np.int32).astype(np.int64)
        for t, vs in found.items():
            for v in vs:
                idx = np.nonzero(tgt == v)[0]
                for i in idx:
                    print(f"  ref {t!r:22s} <- {s['name']}:{s['va'] + int(offs[i]):#x}"
                          f"  (file {s['raw'] + int(offs[i]):#x})")

# ---------------------------------------------------------------- stage 4
print("\n=== searching for float32 tables matching the measured curve ===")
curve = np.load(OUT / "curve_L.npy")
NIN = 384000
probe = curve[:: NIN // 64][:64].astype(np.float32)  # 64 evenly spaced samples
print("  probe (first 8):", probe[:8])

fl = np.frombuffer(data, dtype="<f4")
# candidate anchors: the hard-left value 0.7071067 and the peak 1.0498989
anchors = {
    "peak 1.0498989": np.float32(1.04989886283875),
    "hardleft 0.7071067": np.float32(0.7071067095),
    "hardright 0.7071041": np.float32(0.7071041465),
    "1/sqrt2 exact": np.float32(0.7071067811865476),
    "sqrt2": np.float32(1.4142135623730951),
}
for name, val in anchors.items():
    idx = np.nonzero(fl == val)[0]
    print(f"  {name} = {val!r}: {len(idx)} exact float32 hits", 
          list(idx[:10]))
