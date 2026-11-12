"""EXPLORATORY (not registered): cluster-aware intervals for the external Type 1 counts (4/48 narrow, 16/48 broad).

The 48 applicable sites are not independent: they lie in files and repositories. Reports (i) a Clopper-Pearson interval on the
number of files (and repositories) that contain a positive among files (repositories) with an applicable site, and (ii) a cluster
bootstrap of the site share, resampling files (or repositories) with replacement. Registered labels only.

    python v2/scripts/cluster_intervals.py  ->  v2/results/cluster_intervals.json
"""
import os
import sys
import json
import collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stats_util import clopper_pearson

lab = json.load(open(os.path.join(V2, "evidence_r1", "rebuttal", "results", "task4c_labels.json")))
app = [x for x in lab if x["label"] != "NOT_APPLICABLE"]
for x in app:
    x["narrow"] = x["label"] == "REACHABLE_UNGUARDED"
    x["broad"] = x["narrow"] or (x["label"] in ("UNREACHABLE", "GUARDED") and x["divergence_only"])


def clus(unit):
    by = collections.defaultdict(list)
    for x in app:
        by[(x["repo"], x["file"]) if unit == "file" else x["repo"]].append(x)
    return by


def run(reading, unit, rng, B=10000):
    by = clus(unit)
    keys = list(by)
    pos_units = sum(any(s[reading] for s in by[k]) for k in keys)
    cp = clopper_pearson(pos_units, len(keys))
    arr_pos = np.array([sum(s[reading] for s in by[k]) for k in keys])
    arr_n = np.array([len(by[k]) for k in keys])
    shares = []
    for _ in range(B):
        idx = rng.integers(0, len(keys), len(keys))
        shares.append(arr_pos[idx].sum() / arr_n[idx].sum())
    return {"sites": len(app), "positive_sites": int(arr_pos.sum()), "units": len(keys), "units_with_positive": int(pos_units),
            "cp95_units_with_positive": [round(cp[0], 3), round(cp[1], 3)],
            "cluster_bootstrap95_site_share": [round(float(np.percentile(shares, 2.5)), 3), round(float(np.percentile(shares, 97.5)), 3)]}


rng = np.random.default_rng(20261111)
out = {r: {u: run(r, u, rng) for u in ("file", "repo")} for r in ("narrow", "broad")}
json.dump(out, open(os.path.join(V2, "results", "cluster_intervals.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
