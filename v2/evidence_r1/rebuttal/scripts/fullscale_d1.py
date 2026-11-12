"""Full-scale detector 1: label arrays, whole-cohort kappa, cohort bootstrap, audit draws.

Uses the shipped labelling and bootstrap code unchanged (run_external1.mimic_labels /
eicu_labels / save_labels, bootstrap_kappa.report) but writes only under rebuttal/, so the
demo-scale artifacts in detectors/results/ are not overwritten.

    PCL_TEST_MODE=0 MIMIC_DIR=... EICU_DIR=... python -W ignore rebuttal/scripts/fullscale_d1.py label --out <dir outside repo>
    python -W ignore rebuttal/scripts/fullscale_d1.py boot --labels <dir>/labels.npz --iters 5000

The label arrays are per-stay: keep them outside the repository, on this machine only.
"""
import os
import sys
import json
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np

from detectors.checks.check1_label_shift import KAPPA_FLAG
OUT = os.path.join(ROOT, "rebuttal", "results")
BASE = "SOFA win[-48,+24]"
CTRL = ("SOFA single-point", "SOFA win[-24,+12]", "SOFA win[-72,+24]")


def stage_label(out_dir):
    from detectors.external.run_external1 import mimic_labels, eicu_labels, save_labels
    os.makedirs(out_dir, exist_ok=True)
    m = mimic_labels(verbose=True)
    np.savez_compressed(os.path.join(out_dir, "mimic_partial.npz"), ids=m[0], icd=m[1])
    e = eicu_labels(verbose=True)
    save_labels(os.path.join(out_dir, "labels.npz"), m, e)
    print("labels saved", flush=True)


def stage_boot(path, iters, seed):
    from detectors.external.run_external1 import load_labels
    from detectors.external.bootstrap_kappa import report, audit_subset_distribution
    (m_ids, m_icd, m_sofa), (e_ids, e_icd, e_sofa) = load_labels(path)
    out = {"iters": iters, "seed": seed, "threshold": KAPPA_FLAG,
           "n": {"MIMIC": int(len(m_ids)), "eICU": int(len(e_ids))}, "cases": {}, "prevalence": {}}
    for db, icd, sofa in (("MIMIC", m_icd, m_sofa), ("eICU", e_icd, e_sofa)):
        out["prevalence"][db] = {"ICD": float(np.mean(icd)), **{k: float(np.mean(v)) for k, v in sofa.items()}}
        pairs = [(f"{db} {BASE} vs {c}", sofa[BASE], sofa[c], False) for c in CTRL]
        pairs.append((f"{db} POSITIVE ICD vs SOFA", icd, sofa[BASE], True))
        for name, a, b, positive in pairs:
            r = report(name, a, b, KAPPA_FLAG, iters, seed)
            lo, hi, draws, k_n = audit_subset_distribution(a, b, 500, iters=iters, seed=seed)
            sd = float(np.std(draws, ddof=1))
            r["audit_sd"] = sd
            r["margin_m"] = float(abs(KAPPA_FLAG - r["kappa"]) / sd) if sd > 0 else None
            r["positive"] = positive
            out["cases"][name] = r
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "full_scale_bootstrap_kappa.json"), "w"), indent=1)
    print("wrote rebuttal/results/full_scale_bootstrap_kappa.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["label", "boot"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--labels", default=None)
    ap.add_argument("--iters", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    stage_label(a.out) if a.stage == "label" else stage_boot(a.labels, a.iters, a.seed)
