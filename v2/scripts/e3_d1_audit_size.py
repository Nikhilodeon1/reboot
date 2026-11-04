"""E3 (PREREG_V2.md): detector 1 flag probability against audit size.

    python -W ignore v2/scripts/e3_d1_audit_size.py --labels <labels.npz outside the repo> [--draws 2000] [--out DIR]

Calls the shipped cohens_kappa and the shipped flag rule (kappa < KAPPA_FLAG) unchanged. Writes aggregates only.
"""
import os
import sys
import json
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import numpy as np

from detectors.checks.check1_label_shift import cohens_kappa, KAPPA_FLAG
from detectors.external.run_external1 import load_labels
from stats_util import clopper_pearson, phi

R1 = os.path.join(ROOT, "v2", "evidence_r1", "rebuttal", "results", "full_scale_bootstrap_kappa.json")
SIZES = [100, 200, 500, 1000, 2000, 5000]
BASE = "SOFA win[-48,+24]"
CASES = [  # name, database, which pair, round-1 case key
    ("MIMIC control", "MIMIC", "ctrl", "MIMIC SOFA win[-48,+24] vs SOFA single-point"),
    ("eICU positive", "eICU", "pos", "eICU POSITIVE ICD vs SOFA"),
    ("eICU control", "eICU", "ctrl", "eICU SOFA win[-48,+24] vs SOFA single-point"),
]


def predict(theta, sd500, n, N):
    sd = sd500 * math.sqrt((500.0 / n) * (N - n) / (N - 500))
    return phi((KAPPA_FLAG - theta) / sd), sd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out", default=os.path.join(ROOT, "v2", "results"))
    a = ap.parse_args()
    r1 = json.load(open(R1))
    (m_ids, m_icd, m_sofa), (e_ids, e_icd, e_sofa) = load_labels(a.labels)
    data = {"MIMIC": (m_icd, m_sofa), "eICU": (e_icd, e_sofa)}
    out = {"draws": a.draws, "threshold": KAPPA_FLAG, "sizes": SIZES, "cases": {}}
    for ci, (name, db, kind, key) in enumerate(CASES):
        icd, sofa = data[db]
        x = np.asarray(sofa[BASE], int)
        y = np.asarray(icd if kind == "pos" else sofa["SOFA single-point"], int)
        N = len(x)
        theta, sd500 = r1["cases"][key]["kappa"], r1["cases"][key]["audit_sd"]
        rows = []
        for si, n in enumerate(SIZES):
            rng = np.random.default_rng(90000 + 100 * ci + si)
            flags = und = 0
            ks = []
            for _ in range(a.draws):
                idx = rng.choice(N, size=n, replace=False)
                k = cohens_kappa(x[idx], y[idx])
                if not np.isfinite(k):
                    und += 1
                    continue
                ks.append(float(k))
                flags += int(k < KAPPA_FLAG)
            dec = a.draws - und
            p_hat, sd_n = predict(theta, sd500, n, N)
            rows.append({"n": n, "decidable": dec, "undecidable": und, "flags": flags,
                         "p_obs": flags / dec if dec else None,
                         "cp95": clopper_pearson(flags, dec),
                         "p_hat": p_hat, "sd_model": sd_n,
                         "sd_observed": float(np.std(ks, ddof=1)) if len(ks) > 1 else None,
                         "mean_kappa_draws": float(np.mean(ks)) if ks else None})
            print(f"{name} n={n}: obs {flags}/{dec} = {flags / max(dec, 1):.3f} predicted {p_hat:.3f}", flush=True)
        inside = [r for r in rows if r["n"] in (200, 500, 1000, 2000) and r["p_obs"] is not None]
        D = max(abs(r["p_hat"] - r["p_obs"]) for r in inside)
        reading = "supported" if D <= 0.05 else ("partly supported" if D <= 0.10 else "not supported")
        out["cases"][name] = {"N": N, "theta_star": theta, "sigma_500": sd500, "rows": rows,
                              "D": D, "reading": reading}
    # derived: audit size at which the MIMIC control verdict would be deterministic under the model
    c = out["cases"]["MIMIC control"]
    z = 1.6449
    gap = abs(KAPPA_FLAG - c["theta_star"])
    n_star = None
    for n in range(100, c["N"], 100):
        sd = c["sigma_500"] * math.sqrt((500.0 / n) * (c["N"] - n) / (c["N"] - 500))
        if gap / sd >= z:
            n_star = n
            break
    out["derived"] = {"n_star_mimic_control": n_star, "cohort_size": c["N"],
                      "note": "None means no audit size up to the cohort size gives P(flag) <= 0.05 or >= 0.95"}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e3_d1_audit_size.json"), "w"), indent=1)
    print("wrote e3_d1_audit_size.json; readings:", {k: v["reading"] for k, v in out["cases"].items()},
          "n*:", n_star, flush=True)


if __name__ == "__main__":
    main()
