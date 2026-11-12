"""Task 6: detector 5 restricted to the components present in every database.

Sensitivity analysis only; detector 5's definition, gates and thresholds are not
changed. The same detector code runs twice on identical stays and seeds:

    full        every component the original instantiation uses
    restricted  MAP and Henderson-Hasselbalch (HH) only

PhysioNet: full = MAP, HH, SpO2 (O2Sat vs SaO2); external: full = MAP, HH,
Severinghaus. The restricted set drops the oxygen term, which is circular on
PhysioNet and not comparable externally.

Cases: PhysioNet A vs B (flagship, expected flag) and A vs itself (control);
external eICU halves with HCO3 ablated at 50/80/95% (expected flag), eICU halves
without ablation (control), PhysioNet A vs itself at the external sample size.
Both decision variants (A conjunction, B availability only), 5 seeds.

    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/task6_detector5_restricted.py \
        [--arrays <npz cache outside the repo>]

Per-stay arrays are only cached outside the repository; outputs are aggregates.
"""
import os
import sys
import json
import argparse
import math

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import numpy as np

from detectors.checks.check5_missingness_scale import (
    VARIANTS, run_check_on_stays, scan, sample_files, AVAIL_RATIO_FLAG, COMP_GAP_RATIO_FLAG)
from detectors.external.pipeline5 import ablate, load_site, split_arrays, to_stays
from detectors.external.run_external5 import ABLATION_LEVELS, load_arrays, save_arrays

PHYS_FULL = ["MAP", "HH", "SpO2"]
EXT_FULL = ["MAP", "HH", "Severinghaus"]
RESTRICTED = ["MAP", "HH"]
OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))


def evaluate(A, B, keys):
    """Per rule: flag; shared stats. Undecidable if a side is empty or the aggregate is NaN."""
    row = {}
    stats = None
    for vname, rule in sorted(VARIANTS.items()):
        flagged, st = run_check_on_stays("a", A, "b", B, verbose=False, rule=rule, keys=keys)
        row[vname] = bool(flagged)
        stats = st
    nan = any(not math.isfinite(stats[k]) for k in ("naive_gap", "comp_gap", "composition_gap_ratio"))
    row.update(avail=stats["max_avail_ratio"], gap_ratio=stats["composition_gap_ratio"],
               naive_gap=stats["naive_gap"], comp_gap=stats["comp_gap"],
               n_a=stats["n_stays_a"], n_b=stats["n_stays_b"],
               undecidable=bool(stats["n_stays_a"] == 0 or stats["n_stays_b"] == 0 or nan),
               component_absent_one_side=bool(math.isinf(stats["max_avail_ratio"])))
    return row


def summarise(rows):
    g = np.array([r["gap_ratio"] for r in rows], float)
    a = np.array([r["avail"] for r in rows], float)
    dec = [r for r in rows if not r["undecidable"]]
    out = {"n_seeds": len(rows), "undecidable": len(rows) - len(dec),
           "component_absent_one_side": int(sum(r["component_absent_one_side"] for r in rows)),
           "gap_ratio_mean": float(np.nanmean(g)), "gap_ratio_sd": float(np.nanstd(g, ddof=1)) if len(g) > 1 else None,
           "gap_ratio_min": float(np.nanmin(g)), "gap_ratio_max": float(np.nanmax(g)),
           "avail_mean_finite": (float(np.mean(a[np.isfinite(a)])) if np.isfinite(a).any() else None),
           "gap_ratio_over_gate": int(sum(1 for r in dec if r["gap_ratio"] > COMP_GAP_RATIO_FLAG)),
           "avail_over_gate": int(sum(1 for r in dec if r["avail"] > AVAIL_RATIO_FLAG))}
    for v in sorted(VARIANTS):
        out[f"flags_{v}"] = f"{sum(r[v] for r in dec)}/{len(dec)}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--physionet-n", type=int, nargs="+", default=[900, 1500])
    ap.add_argument("--ext-n", type=int, default=800, help="PhysioNet stays per arm for the external-size control")
    ap.add_argument("--arrays", default=None, help="npz cache of external raw_ts (outside the repo)")
    a = ap.parse_args()
    seeds = list(range(a.seeds))
    res = {"gates": {"availability": AVAIL_RATIO_FLAG, "composition_gap_ratio": COMP_GAP_RATIO_FLAG},
           "seeds": seeds, "physionet": {}, "external": {}}

    for n in a.physionet_n:
        cells = {"full": {"flagship": [], "control": []}, "restricted": {"flagship": [], "control": []}}
        for s in seeds:
            fa, fb = sample_files(s, n)
            A, _ = scan(fa[:n]); B, _ = scan(fb)
            half = len(fa) // 2
            A1, _ = scan(fa[:half]); A2, _ = scan(fa[half:])
            for name, keys in (("full", PHYS_FULL), ("restricted", RESTRICTED)):
                cells[name]["flagship"].append(evaluate(A, B, keys))
                cells[name]["control"].append(evaluate(A1, A2, keys))
            print(f"physionet n={n} seed {s} done", flush=True)
        res["physionet"][str(n)] = {name: {c: summarise(r) for c, r in d.items()} for name, d in cells.items()}

    if a.arrays and os.path.exists(a.arrays):
        eicu, mimic = load_arrays(a.arrays)
    else:
        eicu = load_site("eicu"); mimic = load_site("mimic")
        if a.arrays:
            save_arrays(a.arrays, eicu, mimic)
    res["external"]["n_eicu"], res["external"]["n_mimic"] = len(eicu), len(mimic)
    cases = {}
    for name in ("full", "restricted"):
        cases[name] = {f"E1 ablation {int(p * 100)}%": [] for p in ABLATION_LEVELS}
        cases[name]["E2 eICU split, no ablation"] = []
        cases[name]["E4 PhysioNet A vs itself"] = []
    for s in seeds:
        arm1, arm2 = split_arrays(eicu, s)
        A = to_stays(arm1)
        fa, _ = sample_files(s, a.ext_n)
        half = len(fa) // 2
        P1, _ = scan(fa[:half]); P2, _ = scan(fa[half:])
        for name, ext_keys, phys_keys in (("full", EXT_FULL, PHYS_FULL), ("restricted", RESTRICTED, RESTRICTED)):
            for p in ABLATION_LEVELS:
                cases[name][f"E1 ablation {int(p * 100)}%"].append(
                    evaluate(A, to_stays(ablate(arm2, "HCO3", p=p, seed=s)), ext_keys))
            cases[name]["E2 eICU split, no ablation"].append(evaluate(A, to_stays(arm2), ext_keys))
            cases[name]["E4 PhysioNet A vs itself"].append(evaluate(P1, P2, phys_keys))
        print(f"external seed {s} done", flush=True)
    res["external"]["cases"] = {name: {c: summarise(r) for c, r in d.items()} for name, d in cases.items()}
    res["external"]["E3_descriptive"] = {
        name: evaluate(to_stays(mimic), to_stays(eicu), keys)
        for name, keys in (("full", EXT_FULL), ("restricted", RESTRICTED))}

    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "task6_detector5_restricted.json"), "w"), indent=1)

    def line(tag, s):
        return (f"{tag:<30} gap_ratio {s['gap_ratio_mean']:.3f} (sd {s['gap_ratio_sd'] if s['gap_ratio_sd'] is None else round(s['gap_ratio_sd'],3)},"
                f" {s['gap_ratio_min']:.2f}-{s['gap_ratio_max']:.2f})  avail {s['avail_mean_finite']}  "
                f"A {s['flags_A_conjunction']}  B {s['flags_B_availability_only']}  undec {s['undecidable']}  absent1side {s['component_absent_one_side']}")
    for n, d in res["physionet"].items():
        for name in ("full", "restricted"):
            for c in ("flagship", "control"):
                print(f"PhysioNet n={n:<5} {name:<10} {line(c, d[name][c])}")
    for name in ("full", "restricted"):
        for c, s in res["external"]["cases"][name].items():
            print(f"external {name:<10} {line(c, s)}")


if __name__ == "__main__":
    main()
