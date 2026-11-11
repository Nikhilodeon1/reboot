"""E5 (PREREG_V2_ADDENDUM_3.md): detector 2 dose sweep, shipped statistic (v1) against the volume-matched statistic (v2).

    PCL_TEST_MODE=1 python -W ignore v2/scripts/e5_detector2_dose_sweep.py --seed 42     (one process per seed; seeds 42 to 46)
    python -W ignore v2/scripts/e5_detector2_dose_sweep.py --analyse

The data, split, model and epochs are the round-1 procedure of rebuttal/scripts/task2_values_vs_missingness.py (copied logic, no change to
the detector). Doses 1, 2 and 10 percent are new; 5 and 20 percent are read from the round-1 per-seed files.
"""
import os
import sys
import json
import time
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import numpy as np
import torch

from stats_util import clopper_pearson

CRIT_T = 2.132
NEW_LEVELS = [0.01, 0.02, 0.10]
OLD_LEVELS = ["5", "20"]
SEEDS = [42, 43, 44, 45, 46]
OUT = os.environ.get("V2_E5_OUT", os.path.join(ROOT, "v2", "results", "e5"))
R1 = os.path.join(ROOT, "v2", "evidence_r1", "rebuttal", "results")


def build_with_raw(stays, seed):
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
    hold, _ = load_physionet2019(PHYSIONET_DIR, fraction=0.15, sites=[0], seed=seed + 1000, keep_raw=True)
    src_hold = [x for x in hold if x["patient_id"] not in used]
    assert not used & {x["patient_id"] for x in src_hold}
    tgt_used = [tgt[i] for i in tp[:stays]]
    n_probe = max(50, len(tgt_used) // 4)
    return src_used, src_hold, tgt_used[n_probe:], tgt_used[:n_probe]


def selfcheck(stays, seed, src_used, pool, probe):
    from detectors.checks.check2_pretrain_leakage import build
    s, p, q = build(stays, seed)
    for name, mine, theirs in (("source", src_used, s), ("leak pool", pool, p), ("probe", probe, q)):
        if [x["patient_id"] for x in mine] != [x["patient_id"] for x in theirs.samples]:
            raise SystemExit(f"SELFCHECK FAILED: {name} patient ids differ from check2.build")


def run_seed(seed, stays=900, epochs=3, device="cpu"):
    from src.data.dataset import ICUDataset
    from detectors.checks.check2_pretrain_leakage import run_one
    t0 = time.time()
    src_used, src_hold, pool, probe = build_with_raw(stays, seed)
    selfcheck(stays, seed, src_used, pool, probe)
    src_ds, pool_ds, probe_ds = ICUDataset(src_used), ICUDataset(pool), ICUDataset(probe)
    out = {"seed": seed, "stays": stays, "epochs": epochs, "n_pool": len(pool), "loss": {}, "n_extra": {}, "shortfall": []}
    out["loss"]["A0"], _ = run_one(src_ds, pool_ds, probe_ds, 0.0, seed, epochs, device)
    for frac in NEW_LEVELS:
        n = int(round(frac * len(pool)))
        key = f"{int(round(frac * 100))}"
        if n > len(src_hold) or n < 1:
            out["shortfall"].append({"level": key, "needed": n, "available": len(src_hold)})
            continue
        rng = np.random.default_rng(seed * 1000 + 17)       # same selection rule as the round-1 script
        extra = [src_hold[i] for i in rng.permutation(len(src_hold))[:n]]
        out["n_extra"][key] = n
        out["loss"][f"A1@{key}"], _ = run_one(src_ds, pool_ds, probe_ds, frac, seed, epochs, device)
        out["loss"][f"A2@{key}"], _ = run_one(src_ds, ICUDataset(extra), probe_ds, 1.0, seed, epochs, device)
        print(f"seed {seed} dose {key}% done ({time.time() - t0:.0f}s)", flush=True)
    out["env"] = {"torch": torch.__version__, "numpy": np.__version__}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, f"e5_seed{seed}.json"), "w"), indent=1)
    print("wrote", os.path.join(OUT, f"e5_seed{seed}.json"))


def tstat(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 1e-12 else 0.0


def analyse():
    new = [json.load(open(os.path.join(OUT, f"e5_seed{s}.json"))) for s in SEEDS]
    old = [json.load(open(os.path.join(R1, f"task2_seed{s}.json"))) for s in SEEDS]
    res = {"crit_t": CRIT_T, "seeds": SEEDS, "doses": {}, "note": "doses 5 and 20 from the round-1 per-seed files (same seeds and configuration); doses 1, 2, 10 new"}
    for key, runs in [(f"{int(round(f * 100))}", new) for f in NEW_LEVELS] + [(k, old) for k in OLD_LEVELS]:
        if any(f"A1@{key}" not in r["loss"] for r in runs):
            res["doses"][key] = {"decidable": False}
            continue
        base = np.array([r["loss"]["A0"] for r in runs])
        r1 = (base - np.array([r["loss"][f"A1@{key}"] for r in runs])) / base
        r2 = (base - np.array([r["loss"][f"A2@{key}"] for r in runs])) / base
        res["doses"][key] = {"decidable": True, "r1_mean": float(r1.mean()), "r2_mean": float(r2.mean()),
                             "r2_over_r1": float(r2.mean() / r1.mean()) if r1.mean() > 0 else None,
                             "t_v1": tstat(r1), "t_v2": tstat(r1 - r2),
                             "flag_v1": bool(tstat(r1) >= CRIT_T), "flag_v2": bool(tstat(r1 - r2) >= CRIT_T),
                             "n_extra": runs[0].get("n_extra", {}).get(key)}
    order = sorted((k for k, v in res["doses"].items() if v.get("decidable")), key=int)
    res["lowest_flag_v1"] = next((k for k in order if res["doses"][k]["flag_v1"]), None)
    res["lowest_flag_v2"] = next((k for k in order if res["doses"][k]["flag_v2"]), None)
    res["null_round1"] = {"flags": 1, "of": 20, "cp95": clopper_pearson(1, 20)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(os.path.join(os.path.dirname(OUT), "e5_detector2_dose_sweep.json"), "w"), indent=1)
    for k in order:
        d = res["doses"][k]
        print(f"dose {k:>2}%: r1 {d['r1_mean']:.4f} r2 {d['r2_mean']:.4f} r2/r1 {d['r2_over_r1']} t_v1 {d['t_v1']:.2f} t_v2 {d['t_v2']:.2f} flags v1 {d['flag_v1']} v2 {d['flag_v2']}")
    print("lowest flag v1:", res["lowest_flag_v1"], "v2:", res["lowest_flag_v2"])


if __name__ == "__main__":
    from config import TEST_MODE
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    if a.analyse:
        analyse()
    elif a.seed is not None:
        if not TEST_MODE:
            sys.exit("Run with PCL_TEST_MODE=1: the demonstration tier uses the small model.")
        torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
        run_seed(a.seed)
    else:
        ap.error("give --seed N or --analyse")
