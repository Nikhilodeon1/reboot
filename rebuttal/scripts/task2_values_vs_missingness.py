"""Task 2 (Q-D2): is detector 2's effect carried by values or by missingness?

Arms, per seed, identical probe slice, source set and hyperparameters. L is a
fraction of the target leak pool, the detector's own convention (PREREG D2).

    A0  no leak
    A1  L target stays (values + target missingness): the shipped detector
    A2  L extra SOURCE stays, unmodified (corpus-size control)
    A3  L extra source stays wearing the observation mask of a distinct random
        target stay, applied to raw_ts before forward-fill and normalization
    A4  L extra source stays, randomly masked to the target's per-variable fill

Detector 2 is imported, never edited. A0 and A1 go through the shipped
`run_one` on the shipped `build` split (checked below), so they are the
detector's own numbers on this machine. Extra source stays are the stays loaded
for the source site in a separate draw, with every patient already used for
source training removed by patient id, so they are disjoint from it. (The shipped
draw cannot supply them: roughly half of the sampled files fail the loader's
filters, so it leaves no spare stays.)

Per-seed mode (one process per seed, no shared checkpoint names):

    PCL_TEST_MODE=1 python rebuttal/scripts/task2_values_vs_missingness.py --seed 42

Analysis mode (after all five seeds exist):

    PCL_TEST_MODE=1 python rebuttal/scripts/task2_values_vs_missingness.py --analyse

Outputs are aggregates only: one mean probe loss per arm, level and seed.
"""
import os
import sys
import json
import argparse
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import numpy as np
import torch

CRIT_T = 2.132                    # one-sided 5%, df 4 (five seeds)
LEVELS = [0.05, 0.20]
SEEDS = [42, 43, 44, 45, 46]
ARMS = ["A1", "A2", "A3", "A4"]
OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))


def build_with_raw(stays, seed):
    """Same draw as check2.build, keeping raw_ts and the unused source stays."""
    from src.data.physionet2019 import load_physionet2019
    from config import PHYSIONET_DIR

    frac = min(1.0, (stays * 1.35) / 20000.0)
    src, _ = load_physionet2019(PHYSIONET_DIR, fraction=frac, sites=[0], seed=seed, keep_raw=True)
    tgt, _ = load_physionet2019(PHYSIONET_DIR, fraction=frac, sites=[1], seed=seed, keep_raw=True)
    rng = np.random.default_rng(seed)
    sp = rng.permutation(len(src))
    tp = rng.permutation(len(tgt))
    src_used = [src[i] for i in sp[:stays]]
    used = {x["patient_id"] for x in src_used}
    hold, _ = load_physionet2019(PHYSIONET_DIR, fraction=0.15, sites=[0],
                                 seed=seed + 1000, keep_raw=True)
    src_hold = [x for x in hold if x["patient_id"] not in used]
    assert not used & {x["patient_id"] for x in src_hold}
    tgt_used = [tgt[i] for i in tp[:stays]]
    n_probe = max(50, len(tgt_used) // 4)
    return src_used, src_hold, tgt_used[n_probe:], tgt_used[:n_probe]


def selfcheck(stays, seed, src_used, pool, probe):
    """Fail loudly unless the rebuilt split is the shipped detector's split."""
    from detectors.checks.check2_pretrain_leakage import build
    s, p, q = build(stays, seed)
    for name, mine, theirs in (("source", src_used, s), ("leak pool", pool, p), ("probe", probe, q)):
        ids = [x["patient_id"] for x in mine]
        ref = [x["patient_id"] for x in theirs.samples]
        if ids != ref:
            raise SystemExit(f"SELFCHECK FAILED: {name} patient ids differ from check2.build")
        for a, b in list(zip(mine, theirs.samples))[:5]:
            if not np.allclose(a["values"], b["x"].numpy(), atol=1e-6):
                raise SystemExit(f"SELFCHECK FAILED: {name} values differ from check2.build")


def fill_by_var(raws):
    arr = np.stack(raws)                       # (n, 48, 17)
    return (~np.isnan(arr)).mean(axis=(0, 1))


def make_sample(raw, like):
    from src.data.preprocessing import preprocess_timeseries, MinMaxNormalizer
    r = preprocess_timeseries(raw, MinMaxNormalizer())
    return {"values": r["values"], "mask": r["mask"], "abg_mask": r["abg_mask"],
            "c_mask": r["c_mask"], "label": like["label"], "site_id": like["site_id"],
            "patient_id": like["patient_id"]}


def build_arms(extra, pool, n, seed):
    """Return {arm: [samples]} and per-variable fill diagnostics."""
    from src.data.preprocessing import preprocess_timeseries, MinMaxNormalizer
    rng = np.random.default_rng(seed * 1000 + 17)
    extra = [extra[i] for i in rng.permutation(len(extra))[:n]]

    # sanity: rebuilding an unmasked stay from raw reproduces the stored values
    r0 = preprocess_timeseries(extra[0]["raw_ts"], MinMaxNormalizer())
    assert np.allclose(r0["values"], extra[0]["values"]), "raw rebuild differs from loader"

    tgt_raw = [s["raw_ts"] for s in pool]
    a3_raw = []
    donors = rng.choice(len(pool), size=n, replace=False)     # distinct target stays
    for s, d in zip(extra, donors):
        raw = s["raw_ts"].copy()
        raw[np.isnan(tgt_raw[d])] = np.nan
        a3_raw.append(raw)

    p = fill_by_var(tgt_raw)
    q = fill_by_var([s["raw_ts"] for s in extra])
    keep = np.where(q > 0, np.minimum(1.0, p / np.maximum(q, 1e-12)), 1.0)
    a4_raw = []
    for s in extra:
        raw = s["raw_ts"].copy()
        drop = rng.random(raw.shape) > keep[None, :]
        raw[drop & ~np.isnan(raw)] = np.nan
        a4_raw.append(raw)

    # per-variable raw fill: the target, the unmodified source extras, and what
    # each arm achieved (a mask can only remove observations, never add them)
    diag = {"target_fill": p.tolist(), "A2_fill": q.tolist(),
            "A3_fill": fill_by_var(a3_raw).tolist(),
            "A4_fill": fill_by_var(a4_raw).tolist()}
    arms = {"A2": extra,
            "A3": [make_sample(r, s) for r, s in zip(a3_raw, extra)],
            "A4": [make_sample(r, s) for r, s in zip(a4_raw, extra)]}
    return arms, diag


def run_seed(seed, stays, epochs, device):
    from src.data.dataset import ICUDataset
    from detectors.checks.check2_pretrain_leakage import run_one
    t0 = time.time()
    src_used, src_hold, pool, probe = build_with_raw(stays, seed)
    selfcheck(stays, seed, src_used, pool, probe)
    src_ds, pool_ds, probe_ds = ICUDataset(src_used), ICUDataset(pool), ICUDataset(probe)

    out = {"seed": seed, "stays": stays, "epochs": epochs, "device": device,
           "n_source": len(src_used), "n_pool": len(pool), "n_probe": len(probe),
           "n_holdout": len(src_hold), "loss": {}, "n_extra": {}, "fill": {},
           "shortfall": []}
    out["loss"]["A0"], _ = run_one(src_ds, pool_ds, probe_ds, 0.0, seed, epochs, device)

    for frac in LEVELS:
        n = int(round(frac * len(pool)))
        key = f"{int(frac * 100)}"
        if n > len(src_hold):
            out["shortfall"].append({"level": key, "needed": n, "available": len(src_hold)})
            continue
        out["n_extra"][key] = n
        arms, diag = build_arms(src_hold, pool, n, seed)
        out["fill"][key] = diag
        out["loss"][f"A1@{key}"], _ = run_one(src_ds, pool_ds, probe_ds, frac, seed, epochs, device)
        for arm in ("A2", "A3", "A4"):
            ds = ICUDataset(arms[arm])
            out["loss"][f"{arm}@{key}"], _ = run_one(src_ds, ds, probe_ds, 1.0, seed, epochs, device)
        print(f"seed {seed} level {key}% done ({time.time() - t0:.0f}s)", flush=True)

    out["env"] = {"torch": torch.__version__, "numpy": np.__version__,
                  "python": sys.version.split()[0]}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"task2_seed{seed}.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"wrote {os.path.relpath(path, ROOT)}")


# ---------------------------------------------------------------- analysis

def tstat(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 1e-12 else 0.0


def analyse():
    runs = []
    for s in SEEDS:
        p = os.path.join(OUT, f"task2_seed{s}.json")
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")
        runs.append(json.load(open(p)))
    base = np.array([r["loss"]["A0"] for r in runs])
    res = {"seeds": SEEDS, "A0_mean_loss": float(base.mean()), "levels": {}}
    rows = ["level,arm,mean_r,sd_r,t_vs_A0,per_seed_r"]

    for frac in LEVELS:
        key = f"{int(frac * 100)}"
        if any(f"A1@{key}" not in r["loss"] for r in runs):
            res["levels"][key] = {"decidable": False, "reason": "arms not built (shortfall)"}
            continue
        r = {a: (base - np.array([x["loss"][f"{a}@{key}"] for x in runs])) / base for a in ARMS}
        st = {a: {"mean": float(r[a].mean()), "sd": float(r[a].std(ddof=1)),
                  "t_vs_A0": tstat(r[a]), "per_seed": [float(x) for x in r[a]]} for a in ARMS}
        for a in ARMS:
            rows.append(f"{key},{a},{st[a]['mean']:.5f},{st[a]['sd']:.5f},"
                        f"{st[a]['t_vs_A0']:.3f},{' '.join(f'{x:.4f}' for x in st[a]['per_seed'])}")
        r1, r2, r3, r4 = (r[a].mean() for a in ARMS)
        t12, t32, t13 = tstat(r["A1"] - r["A2"]), tstat(r["A3"] - r["A2"]), tstat(r["A1"] - r["A3"])
        clears = bool(t12 >= CRIT_T)
        R = float((r3 - r2) / (r1 - r2)) if clears else None
        if r1 > 0 and r2 >= 0.5 * r1:
            confounded = True
        else:
            confounded = False
        if R is None:
            verdict = "undetermined"
        elif R <= 0.25 and t32 < CRIT_T:
            verdict = "values-dominated"
        elif R >= 0.75 and t13 < CRIT_T:
            verdict = "missingness-dominated"
        else:
            verdict = "mixed"
        res["levels"][key] = {
            "decidable": True, "arms": st,
            "t_A1_minus_A2": t12, "t_A3_minus_A2": t32, "t_A1_minus_A3": t13,
            "A1_minus_A2_clears_crit": clears, "R": R, "verdict": verdict,
            "corpus_size_confounded": confounded,
            "A3_vs_A4_mean_r": [float(r3), float(r4)],
        }

    res["env"] = runs[0].get("env")
    res["decision_rule_source"] = "rebuttal/PREREG_R1.md section 2 (committed 25fc617)"
    os.makedirs(os.path.join(ROOT, "rebuttal", "tables"), exist_ok=True)
    open(os.path.join(ROOT, "rebuttal", "tables", "task2_arms.csv"), "w").write("\n".join(rows) + "\n")
    json.dump(res, open(os.path.join(OUT, "task2_demo.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "env"}, indent=1)[:4000])


def main():
    from config import TEST_MODE
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1: the demo tier uses the small model.")
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
