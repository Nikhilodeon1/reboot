"""EXPLORATORY (not registered): reference rate for the four-fifths near-threshold counts.

A second mock review asked how many of the 133 public cases would be near the 0.8 threshold if the population ratios were placed at random.
The width of the zone is set by each case's own audit standard deviation at 500 persons, so the reference keeps every case's sigma and
moves the ratios: (i) theta uniform over the observed range of the 133 population ratios, with the zone |0.8 - theta| < 1.64 sigma;
(ii) a permutation of the population ratios across cases (20,000 permutations). The observed count under the same normal-approximation
criterion (margin m <= 1.64) is compared with both. Reads v2/results/e2_public_thresholds.json only.

    python v2/scripts/e2_reference_rate.py -> v2/results/e2_reference_rate.json
"""
import os
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
Z = 1.64
e = json.load(open(os.path.join(V2, "results", "e2_public_thresholds.json")))


def run(subset_name, keep):
    th, sd, mm, pz = [], [], [], []
    for c in e["cases"]:
        if not keep(c):
            continue
        r = next((x for x in c["rows"] if x["n"] == 500), None)
        if r is None:
            continue
        th.append(c["theta_star"]); sd.append(r["sd_R"]); mm.append(r["margin_m"]); pz.append(0.05 <= r["p_flag"] <= 0.95)
    th, sd, mm = np.array(th), np.array(sd), np.array(mm)
    lo, hi = th.min(), th.max()
    uni = np.mean([max(0.0, min(0.8 + Z * s, hi) - max(0.8 - Z * s, lo)) / (hi - lo) for s in sd])
    rng = np.random.default_rng(0)
    cnt = np.array([(np.abs(0.8 - th[rng.permutation(len(th))]) < Z * sd).sum() for _ in range(20000)])
    obs = int((mm <= Z).sum())
    return {"cases": int(len(th)), "observed_in_flag_probability_zone": int(sum(pz)), "observed_m_le_1.64": obs,
            "expected_if_uniform_over_observed_range": float(uni * len(th)),
            "permutation_mean": float(cnt.mean()), "permutation_5_95": [float(np.percentile(cnt, 5)), float(np.percentile(cnt, 95))],
            "permutation_p_observed_or_more": float((cnt >= obs).mean()), "ratio_range": [float(lo), float(hi)], "median_sd_at_500": float(np.median(sd))}


out = {"all_133": run("all", lambda c: True),
       "expected_smaller_group_ge_50": run("ge50", lambda c: 500.0 * min(c["n_group_a"], c["n_group_b"]) / c["N_pop"] >= 50),
       "note": "exploratory; Z = 1.64 normal-approximation zone; the flag-probability count uses the simulated rate between 0.05 and 0.95"}
json.dump(out, open(os.path.join(V2, "results", "e2_reference_rate.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
