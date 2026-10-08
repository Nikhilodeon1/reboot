"""Task 5a: detector 2 and the three standard checks on identical models.

Each (seed, leakage level) model is trained once, by the shipped detector 2
protocol, and everything is read off that one model: detector 2's probe loss and
the baselines' embedding AUROCs. So the stays, levels, seeds, splits and trained
models are identical across the four methods. Thresholds are the shipped ones.

Exploratory addition, labelled as such: NULL replicates. The shipped detector's
0% level is compared against itself (relative delta is exactly 0), so it cannot
flag. Here the 0% arm is also retrained with R other initialisation / shuffle
seeds on the same split, and detector 2's test is applied to each replicate
against the original 0% arm. That is an actual false-positive estimate.

Per seed (one process per seed):

    PCL_TEST_MODE=1 python rebuttal/scripts/task5a_headtohead.py --seed 42

After all five seeds:

    PCL_TEST_MODE=1 python rebuttal/scripts/task5a_headtohead.py --analyse
"""
import os
import sys
import json
import argparse
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "rebuttal", "scripts"))

import numpy as np
import torch

from detectors.checks.check2_pretrain_leakage import LEVELS, build, probe_loss, flag_from_relative
from detectors.baselines.baseline_checks import BASELINES, auroc
from detectors.baselines.run_baselines import embed, fit_logistic, score, kfold_sd
from task1_stats import clopper_pearson

SEEDS = [42, 43, 44, 45, 46]
NULL_REPS = 4
OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))
CKDIR = os.environ.get("CHECKPOINT_DIR", tempfile.gettempdir())


def train_model(src_ds, leak_ds, probe_ds, frac, data_seed, train_seed, epochs, device):
    """Same protocol as check2.run_one, but returns the model."""
    from src.baselines import fresh_model, run_erm_pretraining
    from config import BATCH_SIZE
    from torch.utils.data import DataLoader, Subset, ConcatDataset

    torch.manual_seed(train_seed)
    np.random.seed(train_seed)
    n_leak = int(round(frac * len(leak_ds)))
    if n_leak > 0:
        idx = np.random.default_rng(data_seed).permutation(len(leak_ds))[:n_leak]
        train = ConcatDataset([src_ds, Subset(leak_ds, idx.tolist())])
    else:
        train = src_ds
    tl = DataLoader(train, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    pl = DataLoader(probe_ds, batch_size=BATCH_SIZE, shuffle=False)
    model = fresh_model(seed=train_seed).to(device)
    ck = os.path.join(CKDIR, f"_t5a_{int(frac * 100)}_{data_seed}_{train_seed}.pt")
    run_erm_pretraining(model, tl, pl, n_epochs=epochs, device=device, save_path=ck)
    if os.path.exists(ck):
        os.remove(ck)
    return model, pl


def read_off(model, pl, src_ds, probe_ds, data_seed, device):
    from config import MASK_PROB
    Xs, ys = embed(model, src_ds, device)
    Xt, yt = embed(model, probe_ds, device)
    perm = np.random.default_rng(data_seed).permutation(len(Xs))
    cut = int(0.75 * len(perm))
    tr, te = perm[:cut], perm[cut:]
    sc, clf = fit_logistic(Xs[tr], ys[tr], data_seed)
    return {"probe_loss": probe_loss(model, pl, MASK_PROB, device),
            "kfold_sd": kfold_sd(Xs, ys, data_seed),
            "indomain_auroc": auroc(ys[te], score(sc, clf, Xs[te])),
            "target_auroc": auroc(yt, score(sc, clf, Xt)),
            "n_source": int(len(ys)), "n_target": int(len(yt)),
            "target_prevalence": float(np.mean(yt))}


def run_seed(seed, stays, epochs, device):
    t0 = time.time()
    src_ds, leak_ds, probe_ds = build(stays, seed=seed)
    out = {"seed": seed, "stays": stays, "epochs": epochs, "device": device,
           "levels": {}, "null": []}
    for frac in LEVELS:
        m, pl = train_model(src_ds, leak_ds, probe_ds, frac, seed, seed, epochs, device)
        out["levels"][str(frac)] = read_off(m, pl, src_ds, probe_ds, seed, device)
    for r in range(1, NULL_REPS + 1):
        m, pl = train_model(src_ds, leak_ds, probe_ds, 0.0, seed, seed + 1000 * r, epochs, device)
        out["null"].append(read_off(m, pl, src_ds, probe_ds, seed, device))
    out["env"] = {"torch": torch.__version__, "numpy": np.__version__}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"task5a_seed{seed}.json")
    json.dump(out, open(p, "w"), indent=1)
    print("wrote", os.path.relpath(p, ROOT))


T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776}      # two-sided 95% by df


def tci(x):
    """[mean, lo, hi, n] over the finite entries, t interval with df = n - 1."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return None
    m, s = x.mean(), x.std(ddof=1)
    h = T975[len(x) - 1] * s / np.sqrt(len(x))
    return [float(m), float(m - h), float(m + h), int(len(x))]


def analyse(stays=900, epochs=3):
    runs = []
    for s in SEEDS:
        p = os.path.join(OUT, f"task5a_seed{s}.json")
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")
        runs.append(json.load(open(p)))
    cfg = {(r["stays"], r["epochs"], r["device"], r["env"]["torch"], r["env"]["numpy"]) for r in runs}
    if len(cfg) != 1 or next(iter(cfg))[:2] != (stays, epochs):
        raise SystemExit(f"seed files disagree or not {stays} stays / {epochs} epochs: {sorted(cfg)}")

    lv = lambda key, f: np.array([r["levels"][str(f)][key] for r in runs], float)
    res = {"seeds": SEEDS, "levels": {}, "null": {}}

    # detector 2, paired within seed against the 0% arm
    base = lv("probe_loss", 0.0)
    for f in LEVELS:
        rel = (lv("probe_loss", f) - base) / base
        flagged, t, crit = flag_from_relative(rel) if f > 0 else (False, 0.0, float("inf"))
        res["levels"][str(f)] = {"detector2": {"rel_delta_mean": float(rel.mean()), "t": t,
                                               "flagged": bool(flagged) and f > 0,
                                               "note": "0% compared with itself: cannot flag" if f == 0 else ""}}

    # baselines: per seed flag and decidability, level verdict = majority of decided
    for f in LEVELS:
        row = {}
        for name, fn in BASELINES.items():
            res_s = [fn(r["levels"][str(f)]) for r in runs]
            dec = [fl for fl, ok in res_s if ok]
            k, n = int(sum(dec)), len(dec)
            row[name] = {"flags": k, "decided": n, "undecidable": len(res_s) - n,
                         "flag_rate": (k / n) if n else None,
                         "cp95": clopper_pearson(k, n) if n else None,
                         "verdict": ("UNDECIDABLE" if n == 0 else ("flag" if k > n / 2 else "silent"))}
        res["levels"][str(f)]["baselines"] = row
        res["levels"][str(f)]["summary"] = {
            key: tci(lv(key, f)) for key in ("probe_loss", "kfold_sd", "indomain_auroc", "target_auroc")}

    # signal-to-nuisance: leakage-induced change in target AUROC / 0% source-to-target gap
    gap0 = lv("indomain_auroc", 0.0) - lv("target_auroc", 0.0)
    res["gap0"] = {"per_seed": gap0.tolist(), "mean_ci": tci(gap0)}
    res["gap0"]["interval_contains_zero"] = bool(res["gap0"]["mean_ci"] and
                                                 res["gap0"]["mean_ci"][1] <= 0 <= res["gap0"]["mean_ci"][2])
    for f in LEVELS:
        if f == 0:
            continue
        d = lv("target_auroc", f) - lv("target_auroc", 0.0)
        ok = np.isfinite(d) & np.isfinite(gap0)
        snr = np.where(ok, d / np.where(ok, gap0, 1.0), np.nan)
        res["levels"][str(f)]["snr"] = {
            "n_valid_seeds": int(ok.sum()),
            "delta_target_auroc": tci(d), "per_seed_ratio": [None if not np.isfinite(v) else float(v) for v in snr],
            "mean_ratio_ci": tci(snr),
            "ratio_of_means": float(d[ok].mean() / gap0[ok].mean()) if ok.sum() and gap0[ok].mean() != 0 else None,
            "decidable": bool(ok.sum() >= 3 and not res["gap0"]["interval_contains_zero"]),
            "note": ("denominator interval contains 0, ratio unstable"
                     if res["gap0"]["interval_contains_zero"] else
                     ("fewer than 3 seeds with defined AUROC" if ok.sum() < 3 else ""))}

    # exploratory null replicates for detector 2
    flags, ts = [], []
    for r in range(NULL_REPS):
        rep = np.array([run["null"][r]["probe_loss"] for run in runs], float)
        rel = (rep - base) / base
        fl, t, crit = flag_from_relative(rel)
        flags.append(bool(fl)); ts.append(float(t))
    k = int(sum(flags))
    res["null"] = {"replicates": NULL_REPS, "flags": k, "t": ts, "cp95": clopper_pearson(k, NULL_REPS),
                   "label": "exploratory, not pre-registered"}

    # directional hypothesis: target AUROC against 0%
    res["target_auroc_delta_vs_0"] = {str(f): tci(lv("target_auroc", f) - lv("target_auroc", 0.0))
                                      for f in LEVELS if f > 0}
    res["env"] = runs[0]["env"]
    json.dump(res, open(os.path.join(OUT, "task5a_headtohead.json"), "w"), indent=1)

    print(f"{'level':>6} | detector 2 (rel, t, flag) | " + " | ".join(f"{n} (flags/decided)" for n in BASELINES))
    for f in LEVELS:
        d2 = res["levels"][str(f)]["detector2"]
        b = res["levels"][str(f)]["baselines"]
        print(f"{int(f*100):>5}% | {d2['rel_delta_mean']*100:+6.1f}% t={d2['t']:6.2f} {str(d2['flagged']):>5} | "
              + " | ".join(f"{b[n]['flags']}/{b[n]['decided']} {b[n]['verdict']}" for n in BASELINES))
    print("gap0 (0% source-to-target AUROC gap):", res["gap0"]["mean_ci"], "contains 0:", res["gap0"]["interval_contains_zero"])
    for f in LEVELS[1:]:
        s = res["levels"][str(f)]["snr"]
        print(f"SNR {int(f*100)}%: delta AUROC {s['delta_target_auroc']}  ratio {s['mean_ratio_ci']}  ratio-of-means {s['ratio_of_means']}  decidable {s['decidable']}")
    print("null replicates, detector 2 flags:", res["null"]["flags"], "of", NULL_REPS, "cp95", res["null"]["cp95"])


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
        analyse(a.stays, a.epochs)
    elif a.seed is not None:
        run_seed(a.seed, a.stays, a.epochs, a.device)
    else:
        ap.error("give --seed N or --analyse")


if __name__ == "__main__":
    main()
