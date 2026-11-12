"""Addendum 2, section B: detector 2 null with 20 replicates (exploratory).

A replicate is an independent paired 5-seed comparison of two no-leak arms. For
s = 0..4 a fresh data draw (data seed 5000 + 10r + s) and two models trained on
that same source set, 0% leakage, different model seeds (7000 + 100r + 10s and
7001 + 100r + 10s). Arm Y's probe loss is compared with arm X's within the draw;
the five relative deltas go through the shipped `flag_from_relative`.

    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/addendum2_null20.py --reps 1 2 3 4 5
    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/addendum2_null20.py --analyse
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

from detectors.checks.check2_pretrain_leakage import build, probe_loss, flag_from_relative
from task5a_headtohead import train_model
from task1_stats import clopper_pearson

OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))
N_REPS = 20


def run_rep(r, stays, epochs, device):
    from config import MASK_PROB
    t0 = time.time()
    rel, rows = [], []
    for s in range(5):
        dseed = 5000 + 10 * r + s
        src_ds, leak_ds, probe_ds = build(stays, seed=dseed)
        losses = []
        for tseed in (7000 + 100 * r + 10 * s, 7001 + 100 * r + 10 * s):
            m, pl = train_model(src_ds, leak_ds, probe_ds, 0.0, dseed, tseed, epochs, device)
            losses.append(probe_loss(m, pl, MASK_PROB, device))
        rel.append((losses[1] - losses[0]) / losses[0])
        rows.append({"data_seed": dseed, "loss_x": losses[0], "loss_y": losses[1]})
    flagged, t, crit = flag_from_relative(rel)
    rec = {"rep": r, "flagged": bool(flagged), "t": float(t), "crit": float(crit),
           "rel_deltas": [float(x) for x in rel], "draws": rows, "stays": stays, "epochs": epochs,
           "device": device, "env": {"torch": torch.__version__, "numpy": np.__version__},
           "seconds": round(time.time() - t0, 1)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, f"addendum2_null_rep{r:02d}.json"), "w"), indent=1)
    print(f"rep {r} flagged={flagged} t={t:.2f} ({rec['seconds']}s)", flush=True)


def analyse():
    recs = []
    for r in range(1, N_REPS + 1):
        p = os.path.join(OUT, f"addendum2_null_rep{r:02d}.json")
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")
        recs.append(json.load(open(p)))
    cfg = {(x["stays"], x["epochs"], x["device"], x["env"]["torch"], x["env"]["numpy"]) for x in recs}
    if len(cfg) != 1:
        raise SystemExit(f"replicates disagree on configuration: {sorted(cfg)}")
    k = sum(x["flagged"] for x in recs)
    lo, hi = clopper_pearson(k, N_REPS)
    pooled = np.array([d for x in recs for d in x["rel_deltas"]])
    res = {"label": "exploratory (PREREG_R1_ADDENDUM_2.md section B)", "replicates": N_REPS,
           "flags": k, "cp95": [lo, hi],
           "reading": ("consistent with 5%" if k <= 3 else "limitation: 4 or more flags of 20"),
           "t_per_replicate": [x["t"] for x in recs],
           "pooled_rel_delta_mean": float(pooled.mean()), "pooled_rel_delta_sd": float(pooled.std(ddof=1)),
           "env": recs[0]["env"], "stays": recs[0]["stays"], "epochs": recs[0]["epochs"]}
    json.dump(res, open(os.path.join(OUT, "addendum2_null20.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    from config import TEST_MODE
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1")
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, nargs="+")
    ap.add_argument("--stays", type=int, default=900)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
    if a.analyse:
        analyse()
    elif a.reps:
        for r in a.reps:
            run_rep(r, a.stays, a.epochs, a.device)
    else:
        ap.error("give --reps ... or --analyse")


if __name__ == "__main__":
    main()
