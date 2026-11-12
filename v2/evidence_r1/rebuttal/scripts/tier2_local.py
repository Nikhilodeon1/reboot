"""Task 2 Tier 2 (arms A0, A1, A2) and Task 5b at full scale, on CPU, from existing caches.

Design: PREREG_R1_ADDENDUM_3.md and 3b. Source MIMIC-IV (80% training source, 20% extra-source
hold-out fixed once with permutation seed 0), target eICU, the shipped external protocol
(small test-mode model, 3 epochs, probe = 25% of the target, leak pool = the next block
capped at the source size, seeds 42..46). Arms A3/A4 are not built: the caches hold only
post-forward-fill data.

    python -W ignore rebuttal/scripts/tier2_local.py prepare --mimic-cache A.pkl --eicu-cache B.pkl --out DIR
    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/tier2_local.py run --arrays DIR --seed 42
    PCL_TEST_MODE=1 python -W ignore rebuttal/scripts/tier2_local.py analyse

The arrays in DIR are patient-level derivatives of credentialed data: keep DIR outside the
repository and on this machine. Only aggregates are written under rebuttal/.
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

OUT = os.environ.get("RESULTS_DIR", os.path.join(ROOT, "rebuttal", "results"))
SEEDS = [42, 43, 44, 45, 46]
LEVELS_ARM = [0.05, 0.20]
CRIT_T = 2.132
HOLDOUT_FRAC = 0.20
PROBE_FRAC = 0.25
FIELDS = ("values", "mask", "abg_mask", "c_mask", "sepsis", "mortality_hospital")


def prepare(mimic_cache, eicu_cache, out):
    """Pickled lists of stay dicts -> memory-mappable arrays, one site at a time."""
    os.makedirs(out, exist_ok=True)
    for tag, path in (("mimic", mimic_cache), ("eicu", eicu_cache)):
        with open(path, "rb") as fh:
            stays = pickle.load(fh)
        n = len(stays)
        arr = {"values": np.empty((n, 48, 17), np.float32), "mask": np.empty((n, 48, 17), bool),
               "abg_mask": np.empty((n, 48), bool), "c_mask": np.empty((n, 48, 5), bool),
               "sepsis": np.empty(n, np.uint8), "mortality_hospital": np.empty(n, np.uint8)}
        for i, s in enumerate(stays):
            arr["values"][i] = s["values"]
            arr["mask"][i] = s["mask"]
            arr["abg_mask"][i] = s["abg_mask"]
            arr["c_mask"][i] = s["c_mask"]
            arr["sepsis"][i] = int(np.max(s["label"]) > 0)
            arr["mortality_hospital"][i] = int(s.get("mortality_hospital", 0))
        n_missing = sum("mortality_hospital" not in s for s in stays)
        if n_missing:
            print(f"WARNING {tag}: {n_missing} stays lack mortality_hospital (set to 0)", flush=True)
        del stays
        for k, v in arr.items():
            np.save(os.path.join(out, f"{tag}_{k}.npy"), v)
        print(f"{tag}: {n} stays, sepsis prevalence {arr['sepsis'].mean():.4f}", flush=True)


def load_arrays(d, tag):
    return {k: np.load(os.path.join(d, f"{tag}_{k}.npy"), mmap_mode="r") for k in FIELDS}


class ArrayDS:
    """Dataset over memory-mapped arrays; the keys the training and read-off code use."""

    def __init__(self, arrays, idx):
        import torch
        self.torch = torch
        self.a = arrays
        self.idx = np.asarray(idx)

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, i):
        t, j, a = self.torch, int(self.idx[i]), self.a
        return {"x": t.from_numpy(np.array(a["values"][j], dtype=np.float32)),
                "mask": t.from_numpy(np.array(a["mask"][j])),
                "abg_mask": t.from_numpy(np.array(a["abg_mask"][j])),
                "c_mask": t.from_numpy(np.array(a["c_mask"][j])),
                "sepsis": t.tensor(float(a["sepsis"][j])),
                "mortality_hospital": t.tensor(float(a["mortality_hospital"][j]))}


def embed3(model, dataset, device, batch=256):
    import torch
    from torch.utils.data import DataLoader
    model.eval()
    X, ys, ym = [], [], []
    with torch.no_grad():
        for b in DataLoader(dataset, batch_size=batch, shuffle=False):
            h = model.encode(b["x"].to(device), b["mask"].to(device))
            X.append(h.mean(dim=1).cpu().numpy())
            ys.append(b["sepsis"].cpu().numpy())
            ym.append(b["mortality_hospital"].cpu().numpy())
    return np.concatenate(X), np.concatenate(ys), np.concatenate(ym)


def readoff(model, src_ds, probe_ds, seed, device):
    """Frozen encoder, regularised logistic head fitted on the source, evaluated on the target probe."""
    from detectors.baselines.baseline_checks import auroc
    from detectors.baselines.run_baselines import fit_logistic, score, kfold_sd
    Xs, ss, ms = embed3(model, src_ds, device)
    Xp, sp, mp = embed3(model, probe_ds, device)
    perm = np.random.default_rng(seed).permutation(len(Xs))
    cut = int(0.75 * len(perm))
    tr, te = perm[:cut], perm[cut:]
    out = {}
    for lab, (ysrc, ytgt) in {"sepsis": (ss, sp), "mortality": (ms, mp)}.items():
        if len(np.unique(ysrc[tr])) < 2:       # undecidable, never scored as clean
            out[lab] = {"kfold_sd": float("nan"), "indomain_auroc": float("nan"), "target_auroc": float("nan"),
                        "target_prevalence": float(np.mean(ytgt)), "source_prevalence": float(np.mean(ysrc))}
            continue
        sc, clf = fit_logistic(Xs[tr], ysrc[tr], seed)
        out[lab] = {"kfold_sd": kfold_sd(Xs, ysrc, seed),
                    "indomain_auroc": auroc(ysrc[te], score(sc, clf, Xs[te])),
                    "target_auroc": auroc(ytgt, score(sc, clf, Xp)),
                    "target_prevalence": float(np.mean(ytgt)), "source_prevalence": float(np.mean(ysrc))}
    return out


def run_seed(arr_dir, seed, epochs, device):
    import torch
    from config import MASK_PROB, BATCH_SIZE
    from detectors.checks.check2_pretrain_leakage import probe_loss
    from task5a_headtohead import train_model
    t0 = time.time()
    M, E = load_arrays(arr_dir, "mimic"), load_arrays(arr_dir, "eicu")
    nM, nE = len(M["sepsis"]), len(E["sepsis"])
    perm = np.random.default_rng(0).permutation(nM)
    n_hold = int(round(HOLDOUT_FRAC * nM))
    hold_idx, src_idx = perm[:n_hold], perm[n_hold:]
    tp = np.random.default_rng(seed).permutation(nE)
    n_probe = max(50, int(round(PROBE_FRAC * nE)))
    probe_idx = tp[:n_probe]
    pool_idx = tp[n_probe:n_probe + len(src_idx)]
    src_ds, pool_ds, probe_ds = ArrayDS(M, src_idx), ArrayDS(E, pool_idx), ArrayDS(E, probe_idx)
    print(f"seed {seed}: source {len(src_idx)} hold-out {len(hold_idx)} pool {len(pool_idx)} probe {len(probe_idx)}", flush=True)
    out = {"seed": seed, "epochs": epochs, "device": device, "n_source": int(len(src_idx)),
           "n_holdout": int(len(hold_idx)), "n_pool": int(len(pool_idx)), "n_probe": int(len(probe_idx)),
           "loss": {}, "readoff": {}, "n_extra": {}, "shortfall": [], "steps_per_s": {}}

    def timed(tag, leak_ds, frac, n_train):
        t1 = time.time()
        m, pl = train_model(src_ds, leak_ds, probe_ds, frac, seed, seed, epochs, device)
        dt = time.time() - t1
        out["steps_per_s"][tag] = round(n_train / BATCH_SIZE * epochs / dt, 1)
        print(f"  {tag}: trained in {dt:.0f}s ({out['steps_per_s'][tag]} steps/s)", flush=True)
        return m, pl

    m, pl = timed("A0", pool_ds, 0.0, len(src_idx))
    out["loss"]["A0"] = probe_loss(m, pl, MASK_PROB, device)
    out["readoff"]["A0"] = readoff(m, src_ds, probe_ds, seed, device)
    for frac in LEVELS_ARM + [1.0]:
        key = f"{int(frac * 100)}"
        n = int(round(frac * len(pool_idx)))
        m, pl = timed(f"A1@{key}", pool_ds, frac, len(src_idx) + n)
        out["loss"][f"A1@{key}"] = probe_loss(m, pl, MASK_PROB, device)
        out["readoff"][f"A1@{key}"] = readoff(m, src_ds, probe_ds, seed, device)
        if frac == 1.0:
            continue
        if n > len(hold_idx):
            out["shortfall"].append({"level": key, "needed": n, "available": int(len(hold_idx))})
            continue
        out["n_extra"][key] = n
        extra = np.random.default_rng(seed * 1000 + 17).permutation(hold_idx)[:n]
        m, pl = timed(f"A2@{key}", ArrayDS(M, extra), 1.0, len(src_idx) + n)
        out["loss"][f"A2@{key}"] = probe_loss(m, pl, MASK_PROB, device)
    out["env"] = {"torch": torch.__version__, "numpy": np.__version__}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"tier2local_seed{seed}.json")
    json.dump(out, open(p, "w"), indent=1)
    print("wrote", os.path.relpath(p, ROOT), flush=True)


def tstat(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 1e-12 else 0.0


def analyse():
    from detectors.baselines.baseline_checks import BASELINES
    from detectors.checks.check2_pretrain_leakage import flag_from_relative
    from task5a_headtohead import tci
    from task1_stats import clopper_pearson
    runs = [json.load(open(os.path.join(OUT, f"tier2local_seed{s}.json"))) for s in SEEDS]
    cfg = {(r["epochs"], r["device"], r["env"]["torch"], r["env"]["numpy"], r["n_source"], r["n_holdout"]) for r in runs}
    if len(cfg) != 1:
        raise SystemExit(f"seed files disagree: {sorted(cfg)}")
    base = np.array([r["loss"]["A0"] for r in runs])
    res = {"seeds": SEEDS, "n_source": runs[0]["n_source"], "n_holdout": runs[0]["n_holdout"],
           "n_pool": [r["n_pool"] for r in runs], "A0_mean_loss": float(base.mean()), "env": runs[0]["env"],
           "task2": {}, "task5b": {},
           "note": "A3 and A4 were not built (caches lack the pre-forward-fill series); R is undetermined"}
    for key in ("5", "20"):
        if any(f"A2@{key}" not in r["loss"] for r in runs):
            res["task2"][key] = {"decidable": False, "reason": "A2 not built (shortfall)"}
            continue
        r = {a: (base - np.array([x["loss"][f"{a}@{key}"] for x in runs])) / base for a in ("A1", "A2")}
        st = {a: {"mean": float(r[a].mean()), "sd": float(r[a].std(ddof=1)), "t_vs_A0": tstat(r[a]),
                  "per_seed": [float(x) for x in r[a]]} for a in r}
        r1, r2 = r["A1"].mean(), r["A2"].mean()
        res["task2"][key] = {"decidable": True, "arms": st, "t_A1_minus_A2": tstat(r["A1"] - r["A2"]),
                             "r2_over_r1": float(r2 / r1) if r1 else None,
                             "corpus_size_confounded": bool(r1 > 0 and r2 >= 0.5 * r1), "R": None,
                             "verdict": "undetermined (A3 not built)"}
    for lab in ("sepsis", "mortality"):
        rows = {}
        lv = lambda f, k: np.array([x["readoff"]["A0" if f == "0" else f"A1@{f}"][lab][k] for x in runs], float)
        gap0 = lv("0", "indomain_auroc") - lv("0", "target_auroc")
        for f in ("0", "5", "20", "100"):
            row = {"baselines": {}}
            for name, fn in BASELINES.items():
                rs = [fn(x["readoff"]["A0" if f == "0" else f"A1@{f}"][lab]) for x in runs]
                dec = [fl for fl, ok in rs if ok]
                k, n = int(sum(dec)), len(dec)
                row["baselines"][name] = {"flags": k, "decided": n, "undecidable": len(rs) - n,
                                          "cp95": clopper_pearson(k, n) if n else None}
            if f != "0":
                rel = (np.array([x["loss"][f"A1@{f}"] for x in runs]) - base) / base
                fl, t, crit = flag_from_relative(rel)
                row["detector2"] = {"rel_delta_mean": float(rel.mean()), "t": float(t), "flagged": bool(fl)}
                d = lv(f, "target_auroc") - lv("0", "target_auroc")
                ok = np.isfinite(d) & np.isfinite(gap0)
                row["delta_target_auroc"] = tci(d)
                row["snr_ratio_of_means"] = float(d[ok].mean() / gap0[ok].mean()) if ok.sum() and gap0[ok].mean() else None
            row["target_auroc_mean"] = float(lv(f, "target_auroc").mean())
            rows[f] = row
        res["task5b"][lab] = {"gap0": tci(gap0), "levels": rows}
    json.dump(res, open(os.path.join(OUT, "tier2_local.json"), "w"), indent=1)
    print(json.dumps(res, indent=1)[:5000])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["prepare", "run", "analyse"])
    ap.add_argument("--mimic-cache"); ap.add_argument("--eicu-cache"); ap.add_argument("--out")
    ap.add_argument("--arrays"); ap.add_argument("--seed", type=int)
    ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    if a.stage == "prepare":
        prepare(a.mimic_cache, a.eicu_cache, a.out)
        return
    from config import TEST_MODE
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1")
    import torch
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))
    analyse() if a.stage == "analyse" else run_seed(a.arrays, a.seed, a.epochs, a.device)


if __name__ == "__main__":
    main()
