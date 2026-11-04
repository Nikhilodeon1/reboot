"""E4 (PREREG_V2.md): detector 5, fresh-seed test of the Type 2 prediction.

    PCL_TEST_MODE=1 PHYSIONET_DIR=... python -W ignore v2/scripts/e4_d5_fresh_seeds.py run --n 1200 --seeds 5 6 7
    python -W ignore v2/scripts/e4_d5_fresh_seeds.py analyse

Calls the shipped `run(seed, n)` unchanged. One JSON per (n, seed).
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import numpy as np

from stats_util import clopper_pearson

OUT = os.environ.get("V2_RESULTS", os.path.join(ROOT, "v2", "results", "e4"))
SEEDS = list(range(5, 25))
PRED = {1200: {"p": 0.417, "mean": 0.283, "sd": 0.082}, 4000: {"p": 0.148, "mean": 0.272, "sd": 0.027}}


def run_one(n, s):
    from detectors.checks.check5_missingness_scale import run
    cases = run(seed=s, n=n)
    pos = next(c for c in cases if c.expected)
    neg = next(c for c in cases if not c.expected)
    rec = {"n": n, "seed": s, "positive": dict(pos.stats, flagged=bool(pos.flagged)),
           "negative": dict(neg.stats, flagged=bool(neg.flagged))}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, f"e4_n{n}_s{s}.json"), "w"), indent=1, default=float)
    print(f"n={n} seed={s} ratio={pos.stats['composition_gap_ratio']:.3f} flagged={pos.flagged} "
          f"neg_flagged={neg.flagged}", flush=True)


def analyse():
    res = {"seeds": SEEDS, "per_n": {}}
    for n, pr in PRED.items():
        recs = []
        for s in SEEDS:
            p = os.path.join(OUT, f"e4_n{n}_s{s}.json")
            if not os.path.exists(p):
                raise SystemExit(f"missing {p}")
            recs.append(json.load(open(p)))
        k = sum(r["positive"]["flagged"] for r in recs)
        kneg = sum(r["negative"]["flagged"] for r in recs)
        ratios = np.array([r["positive"]["composition_gap_ratio"] for r in recs], float)
        lo, hi = clopper_pearson(k, len(recs))
        res["per_n"][str(n)] = {
            "predicted_p": pr["p"], "flags": k, "of": len(recs), "cp95": [lo, hi],
            "reading": "consistent" if lo <= pr["p"] <= hi else "not consistent",
            "fresh_ratio_mean": float(ratios.mean()), "fresh_ratio_sd": float(ratios.std(ddof=1)),
            "round1_mean": pr["mean"], "round1_sd": pr["sd"],
            "negative_flags": kneg, "negative_cp95": list(clopper_pearson(kneg, len(recs))),
            "max_avail_ratio_min": float(min(r["positive"].get("max_avail_ratio", float("nan")) for r in recs)),
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(os.path.join(os.path.dirname(OUT), "e4_d5_fresh_seeds.json"), "w"), indent=1)
    print(json.dumps(res["per_n"], indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "analyse"])
    ap.add_argument("--n", type=int)
    ap.add_argument("--seeds", type=int, nargs="*")
    a = ap.parse_args()
    if a.stage == "run":
        for s in a.seeds:
            run_one(a.n, s)
    else:
        analyse()
