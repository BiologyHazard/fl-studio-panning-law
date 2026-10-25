"""Recompute quantitative evidence and file hashes from the archived WAVs."""

import hashlib
import json

import numpy as np
from common import CASES, RESULTS, ROOT, errors, matrix, measured, read_wav


def identity_residual(case):
    p, data = measured(case)
    mask = p > 0
    left, right = data[mask].T
    if case.law == "Circular":
        predicted = (1 - left) * np.sqrt(2 - left**2) / 2
    else:
        predicted = (1 - left) / 2
    return p[mask], right - predicted


def compute():
    input_path = ROOT / "input-wav-file" / "Left Channel DC.wav"
    rate, source = read_wav(input_path)
    if not (np.all(source[:, 0] == 1) and np.all(source[:, 1] == 0)):
        raise ValueError("Input is not exactly [1, 0]")
    result = {
        "input": {
            "rate": rate,
            "frames": len(source),
            "exact_left_one_right_zero": True,
        },
        "pan_convention": "p[n] = -1 + 2*n/N; n=0,...,N-1",
        "cases": {},
        "files": {},
    }
    paths = [input_path]
    for case in CASES:
        fs, data = read_wav(case.path)
        if fs != rate or data.shape != source.shape:
            raise ValueError(f"Incompatible recording: {case.name}")
        p, _ = measured(case)
        residual = data - matrix(p, case)[..., :, 0]
        entry = {
            "rate": fs,
            "frames": len(data),
            "duration_s": len(data) / fs,
            "first": data[0].tolist(),
            "last": data[-1].tolist(),
            "min": data.min(axis=0).tolist(),
            "max": data.max(axis=0).tolist(),
            "right_nonzero_samples": int(np.count_nonzero(data[:, 1])),
            "residual": [errors(residual[:, c]) for c in range(2)],
        }
        if case.control == "Mixer":
            _, r = identity_residual(case)
            entry["positive_pan_identity"] = errors(r)
            entry["identity_samples"] = len(r)
        result["cases"][case.name] = entry
        paths.append(case.path)
    theta = np.arcsin((np.sqrt(34) - np.sqrt(2)) / 8)
    peak = np.sqrt(142 + 34 * np.sqrt(17)) / 16
    result["circular_mixer_peak"] = {
        "pan": float(4 * theta / np.pi - 1),
        "gain": float(peak),
        "dB": float(20 * np.log10(peak)),
    }
    for path in paths + sorted((ROOT / "fl-studio-projects").glob("*.flp")):
        result["files"][path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return result


def main():
    result = compute()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "statistics.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
