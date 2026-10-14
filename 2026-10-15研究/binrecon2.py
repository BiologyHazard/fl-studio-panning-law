"""Second pass: find who references the pan-law strings.

The RIP-relative scan came back empty, so try absolute 32-bit address literals
(the image has a fixed base of 0x400000) and also 8-byte/relocated forms.
Then disassemble around each hit with capstone.
"""

from pathlib import Path
import numpy as np
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DLL = Path(r"C:\Program Files\Image-Line\FL Studio 20\FLEngine_x64.dll")
pe = pefile.PE(str(DLL), fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
N = pe.OPTIONAL_HEADER.SizeOfImage
data = DLL.read_bytes()

secs = []
for s in pe.sections:
    secs.append(dict(
        name=s.Name.rstrip(b"\x00").decode("latin-1"),
        va=BASE + s.VirtualAddress,
        raw=s.PointerToRawData,
        rsize=s.SizeOfRawData,
        vsize=s.Misc_VirtualSize,
        x=bool(s.Characteristics & 0x20000000),
        w=bool(s.Characteristics & 0x80000000),
    ))


def off_to_va(off):
    for s in secs:
        if s["raw"] <= off < s["raw"] + s["rsize"]:
            return s["va"] + (off - s["raw"])
    return None


def va_to_off(va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            return s["raw"] + (va - s["va"])
    return None


TARGETS = ["PanLawLabel", "PanLawSelect", "Circular\x00", "Triangular\x00",
           "Panning law", "Get track pan", "Set track pan",
           "Get channel pan", "Set channel pan", "Center panned signal"]

print("=== string VAs (only those in mapped image sections) ===")
str_va = {}
for t in TARGETS:
    tb = t.encode()
    out = []
    st = 0
    while True:
        i = data.find(tb, st)
        if i < 0:
            break
        v = off_to_va(i)
        if v is not None and v < BASE + N:
            # keep only the canonical occurrence: the most common one in .data
            out.append(v)
        st = i + 1
    str_va[t] = out
    print(f"  {t!r:24s} {[hex(v) for v in out]}")

# choose the .data occurrence for each (strings live in .data by convention)
cand = {}
for t, vs in str_va.items():
    if not vs:
        continue
    for v in vs:
        o = va_to_off(v)
        sname = next(s["name"] for s in secs
                     if s["raw"] <= o < s["raw"] + s["rsize"])
        if sname == ".data":
            cand.setdefault(t, []).append(v)

print("\n=== searching for absolute 32-bit literals equal to those VAs ===")
d32 = np.frombuffer(data, dtype="<u4")
for t, vs in cand.items():
    for v in vs:
        idx = np.nonzero(d32 == v)[0]
        for i in idx:
            ov = off_to_va(int(i))
            sec = next((s["name"] for s in secs
                        if s["raw"] <= i < s["raw"] + s["rsize"]), "?")
            print(f"  {t!r:22s} ref4 @ file {int(i):#x} va {ov if ov else 0:#x} "
                  f"sec {sec}")

print("\n=== searching for absolute 64-bit literals ===")
d64 = np.frombuffer(data[: len(data) // 8 * 8], dtype="<u8")
for t, vs in cand.items():
    for v in vs:
        idx = np.nonzero(d64 == v)[0]
        for i in idx:
            print(f"  {t!r:22s} ref8 @ file {int(i) * 8:#x}")

print("\n=== capstone: disassemble a window around each code hit ===")
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False

hits = []
for t, vs in cand.items():
    for v in vs:
        for i in np.nonzero(d32 == v)[0]:
            ov = off_to_va(int(i))
            if ov is None:
                continue
            sec = next((s for s in secs
                        if s["raw"] <= i < s["raw"] + s["rsize"]), None)
            if sec and sec["x"]:
                hits.append((t, v, int(i), ov))

seen = set()
for t, v, foff, ov in hits:
    start = max(0, foff - 0x60)
    if (start // 16) in seen:
        continue
    seen.add(start // 16)
    print(f"\n--- {t!r} <- va {ov:#x} (file {foff:#x}) ---")
    blob = data[start: foff + 0x40]
    for ins in md.disasm(blob, ov - (foff - start)):
        mark = "  <<<" if ins.address <= ov < ins.address + ins.size else ""
        print(f"  {ins.address:#x}: {ins.mnemonic:8s} {ins.op_str}{mark}")
