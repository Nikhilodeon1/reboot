"""E19b (PREREG_V2_ADDENDUM_15.md): the E19 comparison repeated with the model seeded, random_state 0 to 9.

    python v2/scripts/e19b_seeds.py --data DIR_WITH_Scorecard.csv   ->  v2/results/e19b_seeds.json

The E19 script itself is imported and run unchanged; only the model constructor it uses is given a seed.
"""
import argparse
import contextlib
import functools
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import e19_tableshift_own_file as e19

SEEDS = list(range(10))
GAPS = [f"{kind}_gap_{m}" for kind in ("reported", "true_label") for m in ("accuracy", "auroc", "balanced_accuracy")]


def one_run(data, seed):
    fitted = []

    class Seeded(HistGradientBoostingClassifier):
        def fit(self, X, y, **kw):
            super().fit(X, y, **kw)
            fitted.append({"training_rows": int(len(y)), "iterations": int(self.n_iter_)})
            return self

    e19.HistGradientBoostingClassifier = functools.partial(Seeded, random_state=seed)
    with tempfile.TemporaryDirectory() as tmp:
        argv = sys.argv
        sys.argv = ["e19", "--data", data, "--out", tmp]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                e19.main()
        finally:
            sys.argv = argv
        out = json.load(open(os.path.join(tmp, "e19_tableshift_own_file.json")))
    out["fits"] = dict(zip(("unguarded", "guarded"), fitted))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "results"))
    a = ap.parse_args()
    runs = {}
    for s in SEEDS:
        runs[s] = one_run(a.data, s)
        r = runs[s]["result"]
        print("seed", s, "reported auroc %.4f true-label auroc %.4f" % (r["reported_gap_auroc"]["point"], r["true_label_gap_auroc"]["point"]), flush=True)
    summary = {}
    for g in GAPS:
        points = [runs[s]["result"][g]["point"] for s in SEEDS]
        cis = [runs[s]["result"][g]["ci95"] for s in SEEDS]
        summary[g] = {"median": float(np.median(points)), "min": float(min(points)), "max": float(max(points)),
                      "seeds_interval_above_zero": int(sum(lo > 0 for lo, hi in cis)),
                      "seeds_interval_below_zero": int(sum(hi < 0 for lo, hi in cis))}
    rep = [runs[s]["result"]["reported_gap_auroc"]["point"] for s in SEEDS]
    true = [runs[s]["result"]["true_label_gap_auroc"]["point"] for s in SEEDS]
    bounds = {"reported_auroc_gap_above_0.02": {"seeds_meeting": int(sum(x > 0.02 for x in rep)), "median_meets": bool(np.median(rep) > 0.02)},
              "true_label_auroc_gap_at_most_0.01": {"seeds_meeting": int(sum(x <= 0.01 for x in true)), "median_meets": bool(np.median(true) <= 0.01)}}
    json.dump({"seeds": SEEDS, "summary": summary, "bounds": bounds, "runs": runs},
              open(os.path.join(a.out, "e19b_seeds.json"), "w"), indent=1)
    print(json.dumps({"summary": summary, "bounds": bounds}, indent=1))


if __name__ == "__main__":
    main()
