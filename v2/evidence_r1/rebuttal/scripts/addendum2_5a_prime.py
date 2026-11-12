"""Addendum 2, section C: 5a-prime, downstream AUROC on the full held-out target site.

Same pipeline as Task 5a (PCL_TEST_MODE small model, 900 stays nominal, 3 epochs,
CPU, seeds 42..46, leakage 0/5/20/100%). 5a's encoders were not saved, so each
model is retrained under identical seeds; the retrained probe loss and probe
AUROC are compared with the committed 5a files as an identity check. The target
AUROC is computed on every Site B stay that is not in the seed's drawn target
sample (disjoint from everything used in pretraining).

    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/addendum2_5a_prime.py --seed 42
    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/addendum2_5a_prime.py --analyse
"""
import os
import sys
import json
import argparse
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "rebuttal", "scripts"))

import numpy as np
import torch

from detectors.checks.check2_pretrain_leakage import LEVELS, build, probe_loss
from detectors.baselines.baseline_checks import auroc
from detectors.baselines.run_baselines import embed, fit_logistic, score
from task5a_headtohead import train_model, tci

SEEDS = [42, 43, 44, 45, 46]
OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))


def run_seed(seed, stays, epochs, device):
    from config import PHYSIONET_DIR, MASK_PROB
    from src.data.physionet2019 import load_physionet2019
    from src.data.dataset import ICUDataset
    t0 = time.time()
    src_ds, leak_ds, probe_ds = build(stays, seed=seed)
    used = {s["patient_id"] for s in leak_ds.samples} | {s["patient_id"] for s in probe_ds.samples}
    allb, _ = load_physionet2019(PHYSIONET_DIR, fraction=1.0, sites=[1], seed=0)
    held = [s for s in allb if s["patient_id"] not in used]
    eval_ds = ICUDataset(held)
    print(f"seed {seed}: Site B loaded {len(allb)} stays, held-out {len(held)} ({time.time() - t0:.0f}s)", flush=True)
    out = {"seed": seed, "stays": stays, "epochs": epochs, "device": device, "levels": {},
           "n_site_b": len(allb), "n_heldout": len(held)}
    for frac in LEVELS:
        m, pl = train_model(src_ds, leak_ds, probe_ds, frac, seed, seed, epochs, device)
        Xs, ys = embed(m, src_ds, device)
        Xp, yp = embed(m, probe_ds, device)
        Xe, ye = embed(m, eval_ds, device)
        perm = np.random.default_rng(seed).permutation(len(Xs))
        cut = int(0.75 * len(perm))
        tr, te = perm[:cut], perm[cut:]
        sc, clf = fit_logistic(Xs[tr], ys[tr], seed)
        out["levels"][str(frac)] = {
            "probe_loss": probe_loss(m, pl, MASK_PROB, device),
            "indomain_auroc": auroc(ys[te], score(sc, clf, Xs[te])),
            "target_auroc_probe": auroc(yp, score(sc, clf, Xp)),
            "target_auroc_full": auroc(ye, score(sc, clf, Xe)),
            "n_eval": int(len(ye)), "n_eval_pos": int(ye.sum())}
        print(f"  level {frac}: full-target AUROC {out['levels'][str(frac)]['target_auroc_full']:.4f} "
              f"({int(ye.sum())} positives)", flush=True)
    out["env"] = {"torch": torch.__version__, "numpy": np.__version__}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, f"addendum2_5aprime_seed{seed}.json"), "w"), indent=1)
    print("wrote", f"addendum2_5aprime_seed{seed}.json", flush=True)


def analyse():
    runs = [json.load(open(os.path.join(OUT, f"addendum2_5aprime_seed{s}.json"))) for s in SEEDS]
    ref = [json.load(open(os.path.join(OUT, f"task5a_seed{s}.json"))) for s in SEEDS]
    ident = []
    for a, b in zip(runs, ref):
        for f in LEVELS:
            x, y = a["levels"][str(f)], b["levels"][str(f)]
            ident.append({"seed": a["seed"], "level": f,
                          "d_probe_loss": abs(x["probe_loss"] - y["probe_loss"]),
                          "d_probe_auroc": (abs(x["target_auroc_probe"] - y["target_auroc"])
                                            if np.isfinite(y["target_auroc"]) else None),
                          "d_indomain": (abs(x["indomain_auroc"] - y["indomain_auroc"])
                                         if np.isfinite(y["indomain_auroc"]) else None)})
    lv = lambda k, f: np.array([r["levels"][str(f)][k] for r in runs], float)
    res = {"seeds": SEEDS, "env": runs[0]["env"], "identity_check_max_abs_diff": {
        "probe_loss": max(i["d_probe_loss"] for i in ident),
        "probe_auroc": max(i["d_probe_auroc"] for i in ident if i["d_probe_auroc"] is not None),
        "indomain_auroc": max(i["d_indomain"] for i in ident if i["d_indomain"] is not None)},
        "n_heldout": [r["n_heldout"] for r in runs],
        "n_pos_level0": [r["levels"]["0.0"]["n_eval_pos"] for r in runs], "levels": {}}
    gap0 = lv("indomain_auroc", 0.0) - lv("target_auroc_full", 0.0)
    res["gap0_full"] = {"per_seed": gap0.tolist(), "mean_ci": tci(gap0)}
    for f in LEVELS:
        d = lv("target_auroc_full", f) - lv("target_auroc_full", 0.0)
        row = {"target_auroc_full_mean": float(lv("target_auroc_full", f).mean()),
               "delta_vs_0": tci(d) if f > 0 else None, "delta_per_seed": d.tolist() if f > 0 else None}
        if f > 0 and row["delta_vs_0"]:
            lo, hi = row["delta_vs_0"][1], row["delta_vs_0"][2]
            row["interval_excludes_zero"] = bool(lo > 0 or hi < 0)
        res["levels"][str(f)] = row
    json.dump(res, open(os.path.join(OUT, "addendum2_5aprime.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    from config import TEST_MODE
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--stays", type=int, default=900)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
    if a.analyse:
        analyse()
    elif a.seed is not None:
        run_seed(a.seed, a.stays, a.epochs, a.device)
    else:
        ap.error("give --seed N or --analyse")


if __name__ == "__main__":
    main()
