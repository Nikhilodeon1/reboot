"""Task 2 Tier 2 and Task 5b: full-scale MIMIC-IV -> eICU, same trained models.

Design in PREREG_R1_ADDENDUM_3.md (committed before any run). Source MIMIC-IV,
target eICU, the shipped protocol of detectors/external/run_external2.py (small
test-mode model, 3 epochs). The source is split once (permutation seed 0) into
the training source (80%) and an extra-source hold-out (20%). Per seed (42..46):
the target is permuted, 25% is the probe, the next block (capped at the source
size) is the leak pool.

Arms: A0 no leak; A1 L target stays; A2 L hold-out stays; A3 hold-out stays with
a transplanted target observation mask; A4 hold-out stays masked to the target's
per-variable fill; L = 5% and 20% of the pool. A1 also at 100%. Read-offs for 5b
(baselines on the same A0/A1 models).

    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/tier2_fullscale.py --seed 42 --pool-cache <path>
    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/tier2_fullscale.py --analyse

Raw per-stay data and caches stay outside the repository; outputs are aggregates.
"""
import os
import sys
import json
import time
import pickle
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "rebuttal", "scripts"))

import numpy as np
import torch

from detectors.checks.check2_pretrain_leakage import probe_loss, flag_from_relative
from detectors.baselines.baseline_checks import BASELINES, auroc
from detectors.baselines.run_baselines import fit_logistic, score, kfold_sd
from task5a_headtohead import train_model, tci
from task1_stats import clopper_pearson
from task2_values_vs_missingness import fill_by_var

SEEDS = [42, 43, 44, 45, 46]
LEVELS_ARM = [0.05, 0.20]
OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))
CRIT_T = 2.132
HOLDOUT_FRAC = 0.20
PROBE_FRAC = 0.25


def load_pools_raw(cache):
    if cache and os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    from config import MIMIC_DIR, EICU_DIR
    from src.data.mimic4 import load_mimic4
    from src.data.eicu import load_eicu
    src, _ = load_mimic4(MIMIC_DIR, fraction=1.0, seed=0, keep_raw=True)
    tgt, _ = load_eicu(EICU_DIR, fraction=1.0, seed=0, keep_raw=True)
    if cache:
        os.makedirs(os.path.dirname(cache) or ".", exist_ok=True)
        with open(cache, "wb") as fh:
            pickle.dump((src, tgt), fh, protocol=pickle.HIGHEST_PROTOCOL)
    return src, tgt


def make_sample(raw, like):
    from src.data.preprocessing import preprocess_timeseries, MinMaxNormalizer
    r = preprocess_timeseries(raw, MinMaxNormalizer())
    out = {k: v for k, v in like.items() if k != "raw_ts"}
    out.update(values=r["values"], mask=r["mask"], abg_mask=r["abg_mask"], c_mask=r["c_mask"])
    return out


def build_arms(extra, pool, n, seed):
    """A2 / A3 / A4 samples of size n drawn from the hold-out, plus fill diagnostics."""
    rng = np.random.default_rng(seed * 1000 + 17)
    extra = [extra[i] for i in rng.permutation(len(extra))[:n]]
    tgt_raw = [s["raw_ts"] for s in pool]
    donors = rng.choice(len(pool), size=n, replace=False)
    a3 = []
    for s, d in zip(extra, donors):
        raw = s["raw_ts"].copy()
        raw[np.isnan(tgt_raw[d])] = np.nan
        a3.append(raw)
    p = fill_by_var(tgt_raw)
    q = fill_by_var([s["raw_ts"] for s in extra])
    keep = np.where(q > 0, np.minimum(1.0, p / np.maximum(q, 1e-12)), 1.0)
    a4 = []
    for s in extra:
        raw = s["raw_ts"].copy()
        drop = rng.random(raw.shape) > keep[None, :]
        raw[drop & ~np.isnan(raw)] = np.nan
        a4.append(raw)
    diag = {"target_fill": p.tolist(), "A2_fill": q.tolist(),
            "A3_fill": fill_by_var(a3).tolist(), "A4_fill": fill_by_var(a4).tolist()}
    arms = {"A2": extra,
            "A3": [make_sample(r, s) for r, s in zip(a3, extra)],
            "A4": [make_sample(r, s) for r, s in zip(a4, extra)]}
    return arms, diag


@torch.no_grad()
def embed3(model, dataset, device, batch=256):
    from torch.utils.data import DataLoader
    model.eval()
    X, ys, ym = [], [], []
    for b in DataLoader(dataset, batch_size=batch, shuffle=False):
        h = model.encode(b["x"].to(device), b["mask"].to(device))
        X.append(h.mean(dim=1).cpu().numpy())
        ys.append(b["sepsis"].cpu().numpy())
        ym.append(b["mortality_hospital"].cpu().numpy())
    return np.concatenate(X), np.concatenate(ys), np.concatenate(ym)


def readoff(model, src_ds, probe_ds, seed, device):
    Xs, ss, ms = embed3(model, src_ds, device)
    Xp, sp, mp = embed3(model, probe_ds, device)
    perm = np.random.default_rng(seed).permutation(len(Xs))
    cut = int(0.75 * len(perm))
    tr, te = perm[:cut], perm[cut:]
    out = {}
    for lab, (ysrc, ytgt) in {"sepsis": (ss, sp), "mortality": (ms, mp)}.items():
        sc, clf = fit_logistic(Xs[tr], ysrc[tr], seed)
        out[lab] = {"kfold_sd": kfold_sd(Xs, ysrc, seed),
                    "indomain_auroc": auroc(ysrc[te], score(sc, clf, Xs[te])),
                    "target_auroc": auroc(ytgt, score(sc, clf, Xp)),
                    "target_prevalence": float(np.mean(ytgt)), "source_prevalence": float(np.mean(ysrc))}
    return out


def run_seed(seed, cache, epochs, device, small=False):
    from src.data.dataset import ICUDataset
    from config import MASK_PROB, BATCH_SIZE
    t0 = time.time()
    src_all, tgt_all = load_pools_raw(cache)
    perm = np.random.default_rng(0).permutation(len(src_all))
    n_hold = int(round(HOLDOUT_FRAC * len(src_all)))
    H = [src_all[i] for i in perm[:n_hold]]
    S = [src_all[i] for i in perm[n_hold:]]
    rng = np.random.default_rng(seed)
    tgt = [tgt_all[i] for i in rng.permutation(len(tgt_all))]
    n_probe = max(50, int(round(PROBE_FRAC * len(tgt))))
    probe = tgt[:n_probe]
    pool = tgt[n_probe:n_probe + len(S)]
    print(f"seed {seed}: source {len(S)}  hold-out {len(H)}  pool {len(pool)}  probe {len(probe)}  "
          f"(load {time.time() - t0:.0f}s)", flush=True)
    src_ds, pool_ds, probe_ds = ICUDataset(S), ICUDataset(pool), ICUDataset(probe)

    out = {"seed": seed, "epochs": epochs, "device": device, "n_source": len(S), "n_holdout": len(H),
           "n_pool": len(pool), "n_probe": len(probe), "loss": {}, "readoff": {}, "n_extra": {},
           "fill": {}, "shortfall": [], "steps_per_s": {}}

    def timed(tag, ds_leak, frac, n_train):
        t1 = time.time()
        m, pl = train_model(src_ds, ds_leak, probe_ds, frac, seed, seed, epochs, device)
        dt = time.time() - t1
        out["steps_per_s"][tag] = round(n_train / BATCH_SIZE * epochs / dt, 1)
        print(f"  {tag}: trained in {dt:.0f}s ({out['steps_per_s'][tag]} steps/s)", flush=True)
        return m, pl

    m, pl = timed("A0", pool_ds, 0.0, len(S))
    out["loss"]["A0"] = probe_loss(m, pl, MASK_PROB, device)
    out["readoff"]["A0"] = readoff(m, src_ds, probe_ds, seed, device)

    for frac in LEVELS_ARM + [1.0]:
        key = f"{int(frac * 100)}"
        n = int(round(frac * len(pool)))
        m, pl = timed(f"A1@{key}", pool_ds, frac, len(S) + n)
        out["loss"][f"A1@{key}"] = probe_loss(m, pl, MASK_PROB, device)
        out["readoff"][f"A1@{key}"] = readoff(m, src_ds, probe_ds, seed, device)
        if frac == 1.0:
            continue
        if n > len(H):
            out["shortfall"].append({"level": key, "needed": n, "available": len(H)})
            continue
        out["n_extra"][key] = n
        arms, diag = build_arms(H, pool, n, seed)
        out["fill"][key] = diag
        for arm in ("A2", "A3", "A4"):
            ds = ICUDataset(arms[arm])
            m, pl = timed(f"{arm}@{key}", ds, 1.0, len(S) + n)
            out["loss"][f"{arm}@{key}"] = probe_loss(m, pl, MASK_PROB, device)
    out["env"] = {"torch": torch.__version__, "numpy": np.__version__}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"tier2_seed{seed}.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", os.path.relpath(path, ROOT), flush=True)


def tstat(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 1e-12 else 0.0


def analyse():
    runs = [json.load(open(os.path.join(OUT, f"tier2_seed{s}.json"))) for s in SEEDS]
    cfg = {(r["epochs"], r["device"], r["env"]["torch"], r["env"]["numpy"], r["n_source"], r["n_holdout"]) for r in runs}
    if len(cfg) != 1:
        raise SystemExit(f"seed files disagree on configuration: {sorted(cfg)}")
    base = np.array([r["loss"]["A0"] for r in runs])
    res = {"seeds": SEEDS, "n_source": runs[0]["n_source"], "n_holdout": runs[0]["n_holdout"],
           "n_pool": [r["n_pool"] for r in runs], "A0_mean_loss": float(base.mean()),
           "env": runs[0]["env"], "task2": {}, "task5b": {}}

    for key in ("5", "20"):
        if any(f"A2@{key}" not in r["loss"] for r in runs):
            res["task2"][key] = {"decidable": False, "reason": "arms not built (shortfall)"}
            continue
        arms = ("A1", "A2", "A3", "A4")
        r = {a: (base - np.array([x["loss"][f"{a}@{key}"] for x in runs])) / base for a in arms}
        st = {a: {"mean": float(r[a].mean()), "sd": float(r[a].std(ddof=1)), "t_vs_A0": tstat(r[a]),
                  "per_seed": [float(x) for x in r[a]]} for a in arms}
        r1, r2, r3, r4 = (r[a].mean() for a in arms)
        t12, t32, t13 = tstat(r["A1"] - r["A2"]), tstat(r["A3"] - r["A2"]), tstat(r["A1"] - r["A3"])
        clears = bool(t12 >= CRIT_T)
        R = float((r3 - r2) / (r1 - r2)) if clears else None
        if R is None:
            verdict = "undetermined"
        elif R <= 0.25 and t32 < CRIT_T:
            verdict = "values-dominated"
        elif R >= 0.75 and t13 < CRIT_T:
            verdict = "missingness-dominated"
        else:
            verdict = "mixed"
        res["task2"][key] = {"decidable": True, "arms": st, "t_A1_minus_A2": t12, "t_A3_minus_A2": t32,
                             "t_A1_minus_A3": t13, "A1_minus_A2_clears_crit": clears, "R": R,
                             "verdict": verdict, "corpus_size_confounded": bool(r1 > 0 and r2 >= 0.5 * r1),
                             "r2_over_r1": float(r2 / r1) if r1 else None,
                             "A4_minus_A2_t_exploratory": tstat(r["A4"] - r["A2"])}

    # 5b: detector 2 and the baselines on the same A0 / A1 models
    for lab in ("sepsis", "mortality"):
        rows = {}
        lv = lambda f, k: np.array([x["readoff"][f"A1@{f}" if f != "0" else "A0"][lab][k] for x in runs], float)
        gap0 = lv("0", "indomain_auroc") - lv("0", "target_auroc")
        for f in ("0", "5", "20", "100"):
            row = {"baselines": {}}
            for name, fn in BASELINES.items():
                res_s = [fn(x["readoff"]["A0" if f == "0" else f"A1@{f}"][lab]) for x in runs]
                dec = [fl for fl, ok in res_s if ok]
                k, n = int(sum(dec)), len(dec)
                row["baselines"][name] = {"flags": k, "decided": n, "undecidable": len(res_s) - n,
                                          "cp95": clopper_pearson(k, n) if n else None}
            if f != "0":
                rel = (np.array([x["loss"][f"A1@{f}"] for x in runs]) - base) / base
                fl, t, crit = flag_from_relative(rel)
                row["detector2"] = {"rel_delta_mean": float(rel.mean()), "t": float(t), "flagged": bool(fl)}
                d = lv(f, "target_auroc") - lv("0", "target_auroc")
                ok = np.isfinite(d) & np.isfinite(gap0)
                row["delta_target_auroc"] = tci(d)
                row["snr_ratio_of_means"] = (float(d[ok].mean() / gap0[ok].mean()) if ok.sum() and gap0[ok].mean() else None)
            row["target_auroc_mean"] = float(lv(f, "target_auroc").mean())
            rows[f] = row
        res["task5b"][lab] = {"gap0": tci(gap0), "levels": rows,
                              "target_prevalence_mean": float(np.mean([x["readoff"]["A0"][lab]["target_prevalence"] for x in runs])),
                              "source_prevalence_mean": float(np.mean([x["readoff"]["A0"][lab]["source_prevalence"] for x in runs]))}
    json.dump(res, open(os.path.join(OUT, "tier2_fullscale.json"), "w"), indent=1)
    print(json.dumps(res, indent=1)[:6000])


def main():
    from config import TEST_MODE
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1: the shipped external protocol uses the small model.")
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--pool-cache", default=None, help="pickle of the loaded pools, outside the repo")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--build-cache", action="store_true", help="load the pools, write the cache and exit")
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
    if a.build_cache:
        s, t = load_pools_raw(a.pool_cache)
        print(f"pools: MIMIC {len(s)} stays, eICU {len(t)} stays")
    elif a.analyse:
        analyse()
    elif a.seed is not None:
        run_seed(a.seed, a.pool_cache, a.epochs, a.device)
    else:
        ap.error("give --seed N, --build-cache or --analyse")


if __name__ == "__main__":
    main()
