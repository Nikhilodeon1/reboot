"""E9 and E5-full (PREREG_V2_ADDENDUM_4.md): full-scale missingness arms A3/A4 and the dose sweep with the volume-matched statistic.

    # tasks are independent and resumable: one small json per (seed, task); finished tasks are skipped on rerun
    PCL_TEST_MODE=1 python -W ignore v2/scripts/e9_full_scale.py run --arrays DIR --seed 42 --tasks dose,arms --out RESULTS_DIR [--threads 3]
    python v2/scripts/e9_full_scale.py verify --arrays DIR --out RESULTS_DIR      # one task against the stored round-1 loss
    python v2/scripts/e9_full_scale.py analyse --out RESULTS_DIR --round1 DIR_WITH_tier2local_seed*.json

Arrays in DIR: {mimic,eicu}_{values,mask,abg_mask,c_mask,sepsis,mortality_hospital}.npy as in the full-scale tier, plus for E9
{mimic,eicu}_raw.npy (pre-forward-fill series, float32 with NaN). Patient-level derivatives of credentialed data: keep outside the repository.
The protocol is that of the full-scale tier (small model, 3 epochs, CPU); nothing in the detector is edited.
"""
import os
import sys
import json
import time
import shutil
import argparse
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("PCL_ROOT", os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
import numpy as np

SEEDS = [42, 43, 44, 45, 46]
HOLDOUT_FRAC, PROBE_FRAC, EPOCHS = 0.20, 0.25, 3
CRIT_T = 2.132
DOSES_NEW = [0.01, 0.02, 0.10]
LEVELS_ARMS = [0.05, 0.20]
FIELDS = ("values", "mask", "abg_mask", "c_mask", "sepsis", "mortality_hospital")


def load_arrays(d, tag):
    return {k: np.load(os.path.join(d, f"{tag}_{k}.npy"), mmap_mode="r") for k in FIELDS}


class ArrayDS:
    def __init__(self, arrays, idx):
        import torch
        self.torch, self.a, self.idx = torch, arrays, np.asarray(idx)

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, i):
        t, j, a = self.torch, int(self.idx[i]), self.a
        return {"x": t.from_numpy(np.array(a["values"][j], dtype=np.float32)), "mask": t.from_numpy(np.array(a["mask"][j])),
                "abg_mask": t.from_numpy(np.array(a["abg_mask"][j])), "c_mask": t.from_numpy(np.array(a["c_mask"][j])),
                "sepsis": t.tensor(float(a["sepsis"][j])), "mortality_hospital": t.tensor(float(a["mortality_hospital"][j]))}


def train_model(src_ds, leak_ds, probe_ds, frac, seed, epochs, device, tmp):
    """Same protocol as the full-scale tier (task5a train_model): returns the model and the probe loader."""
    import torch
    from src.baselines import fresh_model, run_erm_pretraining
    from config import BATCH_SIZE
    from torch.utils.data import DataLoader, Subset, ConcatDataset
    torch.manual_seed(seed)
    np.random.seed(seed)
    n_leak = int(round(frac * len(leak_ds)))
    if n_leak > 0:
        idx = np.random.default_rng(seed).permutation(len(leak_ds))[:n_leak]
        train = ConcatDataset([src_ds, Subset(leak_ds, idx.tolist())])
    else:
        train = src_ds
    tl = DataLoader(train, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    pl = DataLoader(probe_ds, batch_size=BATCH_SIZE, shuffle=False)
    model = fresh_model(seed=seed).to(device)
    ck = os.path.join(tmp, f"ck_{os.getpid()}_{int(frac * 100)}_{seed}.pt")
    run_erm_pretraining(model, tl, pl, n_epochs=epochs, device=device, save_path=ck)
    if os.path.exists(ck):
        os.remove(ck)
    return model, pl


def split(arr_dir, seed):
    M, E = load_arrays(arr_dir, "mimic"), load_arrays(arr_dir, "eicu")
    nM, nE = len(M["sepsis"]), len(E["sepsis"])
    perm = np.random.default_rng(0).permutation(nM)
    n_hold = int(round(HOLDOUT_FRAC * nM))
    hold_idx, src_idx = perm[:n_hold], perm[n_hold:]
    tp = np.random.default_rng(seed).permutation(nE)
    n_probe = max(50, int(round(PROBE_FRAC * nE)))
    probe_idx = tp[:n_probe]
    pool_idx = tp[n_probe:n_probe + len(src_idx)]
    return M, E, hold_idx, src_idx, pool_idx, probe_idx


def done_path(out, seed, task):
    return os.path.join(out, f"seed{seed}_{task}.json")


def cpu_model():
    """Processor model and Python version, recorded in every result file (addendum 8)."""
    import platform
    name = platform.processor() or platform.machine()
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    name = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return f"{name}; python {platform.python_version()}"


def write_atomic(path, obj):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1)
    os.replace(tmp, path)


def build_missingness_arms(arr_dir, seed, level, M, E, hold_idx, pool_idx):
    """A3 and A4 extra source stays. Same extras as A2 (first permutation call of rng(seed*1000+17))."""
    from src.data.preprocessing import preprocess_timeseries, MinMaxNormalizer
    n = int(round(level * len(pool_idx)))
    rng = np.random.default_rng(seed * 1000 + 17)
    extra = rng.permutation(hold_idx)[:n]
    mraw = np.load(os.path.join(arr_dir, "mimic_raw.npy"), mmap_mode="r")
    eraw = np.load(os.path.join(arr_dir, "eicu_raw.npy"), mmap_mode="r")
    ex_raw = np.array(mraw[np.sort(extra)])           # sorted for contiguous reads; order restored below
    order = np.argsort(np.argsort(extra))
    ex_raw = ex_raw[order]
    donors = rng.choice(pool_idx, size=n, replace=False)
    d_raw = np.array(eraw[np.sort(donors)])[np.argsort(np.argsort(donors))]
    pool_raw = np.array(eraw[np.sort(pool_idx)])
    p = (~np.isnan(pool_raw)).mean(axis=(0, 1))
    q = (~np.isnan(ex_raw)).mean(axis=(0, 1))
    keep = np.where(q > 0, np.minimum(1.0, p / np.maximum(q, 1e-12)), 1.0)
    a3 = ex_raw.copy()
    a3[np.isnan(d_raw)] = np.nan
    a4 = ex_raw.copy()
    drop = rng.random(a4.shape) > keep[None, None, :]
    a4[drop & ~np.isnan(a4)] = np.nan
    del pool_raw

    def to_arrays(raw):
        vals = np.empty(raw.shape, np.float32)
        msk = np.empty(raw.shape, bool)
        abg = np.empty(raw.shape[:2], bool)
        cm = np.empty(raw.shape[:2] + (5,), bool)
        for i in range(len(raw)):
            r = preprocess_timeseries(np.asarray(raw[i], dtype=float), MinMaxNormalizer())
            vals[i], msk[i], abg[i], cm[i] = r["values"], r["mask"], r["abg_mask"], r["c_mask"]
        z = np.zeros(len(raw), np.uint8)
        return {"values": vals, "mask": msk, "abg_mask": abg, "c_mask": cm, "sepsis": z, "mortality_hospital": z}

    # self-check: the unmasked rebuild of an extra stay reproduces the stored values
    chk = preprocess_timeseries(np.asarray(ex_raw[0], dtype=float), MinMaxNormalizer())
    if not np.allclose(chk["values"], M["values"][extra[0]], atol=1e-6):
        raise SystemExit("SELFCHECK FAILED: raw rebuild differs from the stored values")
    diag = {"target_fill": p.tolist(), "A2_fill": q.tolist(), "A3_fill": (~np.isnan(a3)).mean(axis=(0, 1)).tolist(),
            "A4_fill": (~np.isnan(a4)).mean(axis=(0, 1)).tolist()}
    return to_arrays(a3), to_arrays(a4), diag, n


def run(a):
    import torch
    from config import MASK_PROB
    from detectors.checks.check2_pretrain_leakage import probe_loss
    torch.set_num_threads(a.threads)
    os.makedirs(a.out, exist_ok=True)
    seed = a.seed
    M, E, hold_idx, src_idx, pool_idx, probe_idx = split(a.arrays, seed)
    src_ds, pool_ds, probe_ds = ArrayDS(M, src_idx), ArrayDS(E, pool_idx), ArrayDS(E, probe_idx)
    tmp = tempfile.mkdtemp(prefix="e9_")
    device = "cpu"
    tasks = []
    if "dose" in a.tasks:
        for d in DOSES_NEW:
            tasks += [(f"A1@{int(round(d * 100))}", d, "A1"), (f"A2@{int(round(d * 100))}", d, "A2")]
    if "arms" in a.tasks:
        for d in LEVELS_ARMS:
            tasks += [(f"A3@{int(round(d * 100))}", d, "A3"), (f"A4@{int(round(d * 100))}", d, "A4")]
    if "base" in a.tasks:
        # more seeds (addendum 7): the no-leak arm and the 5% and 20% arms that round 1 stored only for seeds 42 to 46
        tasks += [("A0", 0.0, "A0"), ("A1@5", 0.05, "A1"), ("A2@5", 0.05, "A2"), ("A1@20", 0.20, "A1"), ("A2@20", 0.20, "A2")]
    if a.only:
        tasks = [t for t in tasks if t[0] in a.only.split(",")]
    cache = {}
    for name, frac, arm in tasks:
        path = done_path(a.out, seed, name.replace("@", "_at_"))
        if os.path.exists(path):
            print(f"skip {name} (done)", flush=True)
            continue
        t0 = time.time()
        n = int(round(frac * len(pool_idx)))
        if n > len(hold_idx):
            raise SystemExit(f"shortfall: need {n} extra stays, hold-out has {len(hold_idx)}")
        diag = None
        if arm == "A0":
            m, pl = train_model(src_ds, pool_ds, probe_ds, 0.0, seed, EPOCHS, device, tmp)
        elif arm == "A1":
            m, pl = train_model(src_ds, pool_ds, probe_ds, frac, seed, EPOCHS, device, tmp)
        elif arm == "A2":
            extra = np.random.default_rng(seed * 1000 + 17).permutation(hold_idx)[:n]
            m, pl = train_model(src_ds, ArrayDS(M, extra), probe_ds, 1.0, seed, EPOCHS, device, tmp)
        else:
            key = int(round(frac * 100))
            if key not in cache:
                cache.clear()
                a3, a4, dg, _ = build_missingness_arms(a.arrays, seed, frac, M, E, hold_idx, pool_idx)
                cache[key] = (a3, a4, dg)
            a3, a4, dg = cache[key]
            arrs = a3 if arm == "A3" else a4
            diag = dg
            m, pl = train_model(src_ds, ArrayDS(arrs, np.arange(n)), probe_ds, 1.0, seed, EPOCHS, device, tmp)
        loss = probe_loss(m, pl, MASK_PROB, device)
        write_atomic(path, {"seed": seed, "task": name, "loss": loss, "n_extra": n, "n_source": int(len(src_idx)), "n_pool": int(len(pool_idx)),
                            "n_probe": int(len(probe_idx)), "epochs": EPOCHS, "device": device, "seconds": round(time.time() - t0, 1),
                            "torch": torch.__version__, "numpy": np.__version__, "cpu": cpu_model(), "fill": diag})
        print(f"{name} seed {seed}: loss {loss:.6f} in {time.time() - t0:.0f}s", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)


def verify(a):
    """Retrain one stored task and compare with the round-1 loss."""
    a.seed, a.tasks, a.only = 42, "none", None
    import torch
    from config import MASK_PROB
    from detectors.checks.check2_pretrain_leakage import probe_loss
    torch.set_num_threads(a.threads)
    M, E, hold_idx, src_idx, pool_idx, probe_idx = split(a.arrays, 42)
    n = int(round(0.05 * len(pool_idx)))
    extra = np.random.default_rng(42 * 1000 + 17).permutation(hold_idx)[:n]
    tmp = tempfile.mkdtemp(prefix="e9v_")
    m, pl = train_model(ArrayDS(M, src_idx), ArrayDS(M, extra), ArrayDS(E, probe_idx), 1.0, 42, EPOCHS, "cpu", tmp)
    loss = probe_loss(m, pl, MASK_PROB, "cpu")
    ref = json.load(open(os.path.join(a.round1, "tier2local_seed42.json")))["loss"]["A2@5"]
    res = {"retrained_A2@5_seed42": loss, "stored": ref, "abs_diff": abs(loss - ref), "threads": a.threads}
    write_atomic(os.path.join(a.out, "verify_A2_at_5_seed42.json"), res)
    print(res, flush=True)


def tstat(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1)
    return float(d.mean() / (sd / np.sqrt(len(d)))) if sd > 1e-12 else 0.0


def analyse(a):
    from scipy import stats as _st
    SEEDS_ = [int(x) for x in a.seeds.split(",")] if a.seeds else SEEDS
    crit = float(_st.t.ppf(0.95, len(SEEDS_) - 1))
    r1 = {s: json.load(open(os.path.join(a.round1, f"tier2local_seed{s}.json"))) for s in SEEDS_
          if os.path.exists(os.path.join(a.round1, f"tier2local_seed{s}.json"))}
    cfg = {(r["epochs"], r["device"], r["env"]["torch"], r["env"]["numpy"], r["n_source"], r["n_holdout"], r["n_pool"] if False else 0) for r in r1.values()}
    if len(cfg) != 1:
        raise SystemExit(f"round-1 seed files disagree: {sorted(cfg)}")
    def get(s, name):
        if s in r1 and name in r1[s]["loss"]:
            return r1[s]["loss"][name]
        p = done_path(a.out, s, name.replace("@", "_at_"))
        return json.load(open(p))["loss"] if os.path.exists(p) else None

    base_l = [get(s, "A0") for s in SEEDS_]
    base = None if any(x is None for x in base_l) else np.array(base_l)

    def red(name):
        v = [get(s, name) for s in SEEDS_]
        return None if (base is None or any(x is None for x in v)) else (base - np.array(v)) / base
    out = {"seeds": SEEDS_, "critical_t_one_sided_5pct": crit, "dose_sweep": {}, "missingness": {}}
    for d in (1, 2, 5, 10, 20):
        A1, A2 = red(f"A1@{d}"), red(f"A2@{d}")
        if A1 is None or A2 is None:
            out["dose_sweep"][str(d)] = {"complete": False}
            continue
        r1m, r2m = float(A1.mean()), float(A2.mean())
        out["dose_sweep"][str(d)] = {"complete": True, "r1": r1m, "r2": r2m, "r2_over_r1": r2m / r1m if r1m else None,
                                     "t_v1": tstat(A1), "t_v2": tstat(A1 - A2), "v1_flags": bool(tstat(A1) >= crit),
                                     "v2_flags": bool(tstat(A1 - A2) >= crit), "r2_within_0.005_of_zero": bool(abs(r2m) <= 0.005)}
    for d in (5, 20):
        A1, A2, A3, A4 = (red(f"{x}@{d}") for x in ("A1", "A2", "A3", "A4"))
        if any(x is None for x in (A1, A2, A3, A4)):
            out["missingness"][str(d)] = {"complete": False}
            continue
        t12, t32, t13 = tstat(A1 - A2), tstat(A3 - A2), tstat(A1 - A3)
        clears = bool(t12 >= crit)
        r1m, r2m, r3m, r4m = (float(x.mean()) for x in (A1, A2, A3, A4))
        R = (r3m - r2m) / (r1m - r2m) if clears else None
        if R is None:
            verdict = "undetermined"
        elif R <= 0.25 and t32 < crit:
            verdict = "values-dominated"
        elif R >= 0.75 and t13 < crit:
            verdict = "missingness-dominated"
        else:
            verdict = "mixed"
        out["missingness"][str(d)] = {"complete": True, "r1": r1m, "r2": r2m, "r3": r3m, "r4": r4m, "t_A1_minus_A2": t12,
                                      "t_A3_minus_A2": t32, "t_A1_minus_A3": t13, "R": R, "verdict": verdict}
    path = os.path.join(a.out, "e9_e5full_summary.json" if not a.seeds else "e9_more_seeds_summary.json")
    write_atomic(path, out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "verify", "analyse"])
    ap.add_argument("--arrays")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tasks", default="dose,arms")
    ap.add_argument("--only", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round1")
    ap.add_argument("--seeds", default=None, help="analyse: comma-separated seeds (default 42..46)")
    ap.add_argument("--threads", type=int, default=3)
    args = ap.parse_args()
    if args.mode in ("run", "verify") and os.environ.get("PCL_TEST_MODE", "1") != "1":
        sys.exit("Run with PCL_TEST_MODE=1 (the small-model protocol).")
    {"run": run, "verify": verify, "analyse": analyse}[args.mode](args)
