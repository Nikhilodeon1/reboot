"""E16 analysis (addenda 7 and 8): 20-seed values, Fieller intervals for r2/r1, and the single-processor sensitivity analysis.

    python v2/scripts/e16_analysis.py   ->  v2/results/e16_summary.json

Inputs are aggregate losses only. A0 and the 5% and 20% A1/A2 arms of seeds 42 to 46 come from the round-1 files in
v2/evidence_r1; the other arms of those seeds are in v2/results/e16_seeds42_46; seeds 47 to 61 are in v2/results/e16.
This script was used from outside the repository when E16 was analysed and was added to it afterwards, with the paths
made relative.
"""
import json
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from ratio_interval import fieller

R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")
OLD = os.path.join(V2, "results", "e16_seeds42_46")
NEW = os.path.join(V2, "results", "e16")


def loss(s, name):
    if s <= 46:
        j = json.load(open(os.path.join(R1, f"tier2local_seed{s}.json")))["loss"]
        if name in j:
            return j[name]
    folder = OLD if s <= 46 else NEW
    return json.load(open(os.path.join(folder, f"seed{s}_{name.replace('@', '_at_')}.json")))["loss"]


def tstat(d):
    d = np.asarray(d, float)
    return float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))))


def analyse(seeds):
    n = len(seeds)
    crit = float(stats.t.ppf(0.95, n - 1))
    base = np.array([loss(s, "A0") for s in seeds])
    red = lambda nm: (base - np.array([loss(s, nm) for s in seeds])) / base
    out = {"n_seeds": n, "crit": crit, "dose": {}, "miss": {}}
    for d in (2, 5, 20):
        A1, A2 = red(f"A1@{d}"), red(f"A2@{d}")
        f = fieller(A1, A2)
        out["dose"][d] = {"r1": float(A1.mean()), "r2": float(A2.mean()), "ratio": float(A2.mean() / A1.mean()),
                          "fieller95": f[0] if f else None, "t_shipped": tstat(A1), "t_shipped_minus_corpus": tstat(A1 - A2),
                          "shipped_flags": bool(tstat(A1) >= crit), "r1_sd": float(A1.std(ddof=1)), "r2_sd": float(A2.std(ddof=1))}
    for d in (5, 20):
        A1, A2, A3, A4 = (red(f"{x}@{d}") for x in ("A1", "A2", "A3", "A4"))
        r1m, r2m, r3m, r4m = (float(x.mean()) for x in (A1, A2, A3, A4))
        out["miss"][d] = {"r3": r3m, "r4": r4m, "R": (r3m - r2m) / (r1m - r2m), "t_A3_minus_A2": tstat(A3 - A2),
                          "t_A1_minus_A3": tstat(A1 - A3), "A3_minus_A2_clears": bool(tstat(A3 - A2) >= crit)}
    return out


def main():
    res = {"all20": analyse(list(range(42, 62))), "colab14": analyse(list(range(48, 62))),
           "desktop6": analyse(list(range(42, 48))), "five_seed_reference": analyse(list(range(42, 47)))}
    stored, colab = loss(42, "A0"), json.load(open(os.path.join(NEW, "hardware_check_seed42_A0_colab.json")))["loss"]
    res["hardware_check_A0_seed42"] = {"desktop": stored, "colab": colab, "relative_difference": (colab - stored) / stored}
    # the shift in A0 between the two machines is measured at seed 42 only
    json.dump(res, open(os.path.join(V2, "results", "e16_summary.json"), "w"), indent=1)
    for k, v in res.items():
        if k == "hardware_check_A0_seed42":
            print(k, v)
            continue
        print("==", k, "n", v["n_seeds"], "crit %.3f" % v["crit"])
        for d, x in v["dose"].items():
            print(" dose %s r2/r1 %.2f t_shipped %.2f flags %s" % (d, x["ratio"], x["t_shipped"], x["shipped_flags"]))
        for d, x in v["miss"].items():
            print(" miss %s R %.3f tA3-A2 %.2f clears %s" % (d, x["R"], x["t_A3_minus_A2"], x["A3_minus_A2_clears"]))


if __name__ == "__main__":
    main()
