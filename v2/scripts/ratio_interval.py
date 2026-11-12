"""EXPLORATORY (not registered): Fieller 95% interval for r2/r1, the corpus-size control effect as a fraction of detector 2's effect,
from the archived per-seed relative probe-loss reductions (five seeds, paired by seed, df 4).

    python v2/scripts/ratio_interval.py   ->  v2/results/ratio_interval.json
"""
import os
import json
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")


def fieller(x, y, level=0.95):
    """Interval for mu_y / mu_x from paired samples (x = r1 per seed, y = r2 per seed)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    t = stats.t.ppf(0.5 + level / 2, n - 1)
    mx, my = x.mean(), y.mean()
    vxx, vyy, vxy = x.var(ddof=1) / n, y.var(ddof=1) / n, np.cov(x, y, ddof=1)[0, 1] / n
    # (my - R mx)^2 <= t^2 (vyy - 2 R vxy + R^2 vxx)
    a = mx ** 2 - t ** 2 * vxx
    b = -2 * (mx * my - t ** 2 * vxy)
    c = my ** 2 - t ** 2 * vyy
    if a <= 0:
        return None  # r1 not distinguishable from zero: the interval is unbounded
    disc = b * b - 4 * a * c
    r = [(-b - disc ** 0.5) / (2 * a), (-b + disc ** 0.5) / (2 * a)]
    return [float(min(r)), float(max(r))], float(my / mx)


def main():
    out = {}
    d = json.load(open(os.path.join(R1, "task2_demo.json")))["levels"]
    f = json.load(open(os.path.join(R1, "tier2_local.json")))["task2"]
    for scale, src in (("demonstration", d), ("full", f)):
        for lvl in ("5", "20"):
            arms = src[lvl]["arms"]
            res = fieller(arms["A1"]["per_seed"], arms["A2"]["per_seed"])
            out[f"{scale}_{lvl}pct"] = ({"ratio": res[1], "fieller95": res[0], "prereg_line": 0.5,
                                         "interval_includes_line": bool(res[0][0] <= 0.5 <= res[0][1])} if res else {"fieller95": None})
    json.dump(out, open(os.path.join(V2, "results", "ratio_interval.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
