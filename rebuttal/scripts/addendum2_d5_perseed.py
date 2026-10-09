"""Addendum 2, section D: per-seed archive of detector 5's flagship composition ratio.

Runs the shipped `run(seed, n)` (positive PhysioNet A vs B, negative A vs itself,
variant A conjunction) unchanged, as detectors/check5_sampling_sensitivity.py
does, and archives the per-seed values that were not kept. Then the Type 2
prediction P(flag) = Phi((mean - 0.30) / sd) against the observed flag counts.

    python -W ignore rebuttal/scripts/addendum2_d5_perseed.py --n 4000 --seeds 0 1
    python -W ignore rebuttal/scripts/addendum2_d5_perseed.py --analyse
"""
import os
import sys
import json
import math
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "rebuttal", "scripts"))
import numpy as np

from detectors.checks.check5_missingness_scale import run, COMP_GAP_RATIO_FLAG, AVAIL_RATIO_FLAG
from task1_stats import clopper_pearson

OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))
phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def one(n, s):
    cases = run(seed=s, n=n)
    pos = next(c for c in cases if c.expected)
    neg = next(c for c in cases if not c.expected)
    rec = {"n": n, "seed": s,
           "positive": dict(pos.stats, flagged=bool(pos.flagged)),
           "negative": dict(neg.stats, flagged=bool(neg.flagged))}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, f"addendum2_d5_n{n}_s{s}.json"), "w"), indent=1)
    print(f"n={n} seed={s} ratio={pos.stats['composition_gap_ratio']:.3f} avail={pos.stats['max_avail_ratio']:.1f} flagged={pos.flagged}", flush=True)


def pred(mean, sd):
    return phi((mean - COMP_GAP_RATIO_FLAG) / sd)


def analyse():
    res = {"gate": COMP_GAP_RATIO_FLAG, "per_n": {}, "from_archived_summary": {}, "task6": {}}
    # hand-estimate check, from the summary statistics in docs/RESULTS_NOTES.md
    for n, (mean, sd, k, m) in {"1200": (0.283, 0.082, 2, 5), "4000": (0.274, 0.036, 0, 3)}.items():
        res["from_archived_summary"][n] = {"mean": mean, "sd": sd, "predicted_P_flag": pred(mean, sd),
                                           "observed": f"{k}/{m}", "observed_cp95": clopper_pearson(k, m)}
    # Task 6 sizes, from the committed five-seed results
    t6 = json.load(open(os.path.join(OUT, "task6_detector5_restricted.json")))
    for n, d in t6["physionet"].items():
        s = d["full"]["flagship"]
        res["task6"][n] = {"mean": s["gap_ratio_mean"], "sd": s["gap_ratio_sd"],
                           "predicted_P_flag": pred(s["gap_ratio_mean"], s["gap_ratio_sd"]),
                           "observed": s["flags_A_conjunction"]}
    for n in (1200, 4000):
        recs = []
        for s in range(5):
            p = os.path.join(OUT, f"addendum2_d5_n{n}_s{s}.json")
            if os.path.exists(p):
                recs.append(json.load(open(p)))
        if not recs:
            continue
        r = np.array([x["positive"]["composition_gap_ratio"] for x in recs])
        fl = sum(x["positive"]["flagged"] for x in recs)
        neg = np.array([x["negative"]["composition_gap_ratio"] for x in recs])
        res["per_n"][str(n)] = {
            "seeds": [x["seed"] for x in recs], "positive_ratio_per_seed": r.tolist(),
            "positive_avail_per_seed": [x["positive"]["max_avail_ratio"] for x in recs],
            "positive_flags": f"{fl}/{len(recs)}", "positive_flags_cp95": clopper_pearson(fl, len(recs)),
            "mean": float(r.mean()), "sd": float(r.std(ddof=1)), "min": float(r.min()), "max": float(r.max()),
            "predicted_P_flag": pred(float(r.mean()), float(r.std(ddof=1))),
            "negative_ratio_per_seed": neg.tolist(),
            "negative_flags": f"{sum(x['negative']['flagged'] for x in recs)}/{len(recs)}",
            "first3_ratio_per_seed": r[:3].tolist()}
    json.dump(res, open(os.path.join(OUT, "addendum2_d5_perseed.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int)
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    if a.analyse:
        analyse()
    else:
        for s in a.seeds:
            one(a.n, s)


if __name__ == "__main__":
    main()
