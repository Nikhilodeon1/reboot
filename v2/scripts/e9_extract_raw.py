"""E9 stage 1 (PREREG_V2_ADDENDUM_4.md): re-extract the hourly series before forward-fill for the full-scale cohorts.

    python -W ignore v2/scripts/e9_extract_raw.py --site mimic --data <mimiciv/3.1> --arrays DIR   # writes DIR/mimic_raw.npy
    python -W ignore v2/scripts/e9_extract_raw.py --site eicu  --data <eicu-crd/2.0> --arrays DIR   # writes DIR/eicu_raw.npy

Runs the shipped `load_mimic4` / `load_eicu` unchanged (fraction 1.0, seed 0, keep_raw=True). Only the sepsis-label call, whose output is not
used here, is replaced by a stub in this script. Validation before the file is written: the number of stays equals the stored arrays, and
preprocessing every raw series with the shipped `preprocess_timeseries` reproduces the stored `values`, `mask`, `abg_mask` and `c_mask`
(max absolute difference 1e-6). Resumable at site level; the output is written atomically. Patient-level: keep outside the repository.
"""
import os
import sys
import time
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=["mimic", "eicu"], required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--arrays", required=True)
    a = ap.parse_args()
    out = os.path.join(a.arrays, f"{a.site}_raw.npy")
    if os.path.exists(out):
        print("already done", flush=True)
        return
    t0 = time.time()
    if a.site == "mimic":
        import src.data.mimic4 as mod
        mod.mimic_sofa_sepsis_labels = lambda *args, **kw: ({}, {})
        samples, _ = mod.load_mimic4(a.data, fraction=1.0, seed=0, keep_raw=True)
    else:
        import src.data.eicu as mod
        mod.eicu_sofa_sepsis_labels = lambda *args, **kw: ({}, {})
        samples, _ = mod.load_eicu(a.data, fraction=1.0, seed=0, keep_raw=True)
    n = len(samples)
    print(f"loaded {n} stays in {time.time() - t0:.0f}s", flush=True)
    ref_vals = np.load(os.path.join(a.arrays, f"{a.site}_values.npy"), mmap_mode="r")
    if n != len(ref_vals):
        raise SystemExit(f"VALIDATION FAILED: {n} stays loaded, stored arrays have {len(ref_vals)}")
    ref = {k: np.load(os.path.join(a.arrays, f"{a.site}_{k}.npy"), mmap_mode="r") for k in ("mask", "abg_mask", "c_mask")}
    from src.data.preprocessing import preprocess_timeseries, MinMaxNormalizer
    raw = np.empty((n, 48, 17), np.float32)
    worst = 0.0
    for i, s in enumerate(samples):
        r = np.asarray(s["raw_ts"], dtype=float)
        res = preprocess_timeseries(r, MinMaxNormalizer())
        worst = max(worst, float(np.max(np.abs(res["values"] - ref_vals[i]))))
        if worst > 1e-6 or not (np.array_equal(res["mask"], ref["mask"][i]) and np.array_equal(res["abg_mask"], ref["abg_mask"][i])
                                and np.array_equal(res["c_mask"], ref["c_mask"][i])):
            raise SystemExit(f"VALIDATION FAILED at stay index {i}: preprocessed raw series differ from the stored arrays (max abs diff {worst})")
        raw[i] = r
    tmp = out + ".tmp.npy"
    np.save(tmp, raw)
    os.replace(tmp, out)
    print(f"validated {n} stays (max abs diff {worst:.2e}); wrote {out} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
