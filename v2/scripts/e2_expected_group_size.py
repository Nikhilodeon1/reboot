"""EXPLORATORY (not registered): E2 restricted by the expected size of the smaller group inside a 500-person audit.

The first exploratory restriction in the paper used the population size of the smaller group (at least 2,000 persons). A mock review
noted that what matters for a 500-person audit is the expected number of persons of the smaller group in the audit,
500 * min(n_a, n_b) / N_pop. Reads v2/results/e2_public_thresholds.json only.

    python v2/scripts/e2_expected_group_size.py -> v2/results/e2_expected_group_size.json
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stats_util import clopper_pearson

e = json.load(open(os.path.join(V2, "results", "e2_public_thresholds.json")))
out = {}
for thr in (25, 50, 100, 200):
    sel = []
    for c in e["cases"]:
        exp_small = 500.0 * min(c["n_group_a"], c["n_group_b"]) / c["N_pop"]
        if exp_small >= thr:
            row = next(r for r in c["rows"] if r["n"] == 500)
            sel.append((c["case"], exp_small, row["p_flag"], row["margin_m"]))
    k_zone = sum(0.05 <= p <= 0.95 for _, _, p, _ in sel)
    k_m = sum(m <= 3 for _, _, _, m in sel)
    n = len(sel)
    out[f"expected_smaller_group_at_least_{thr}"] = {
        "cases": n,
        "coin_flip_zone": [k_zone, n, [round(x, 3) for x in clopper_pearson(k_zone, n)] if n else None],
        "m_le_3": [k_m, n, [round(x, 3) for x in clopper_pearson(k_m, n)] if n else None]}
json.dump(out, open(os.path.join(V2, "results", "e2_expected_group_size.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
