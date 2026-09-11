"""Detector 2 external validation: MIMIC-IV source -> eICU target.

Uses sample["values"]. Normalization is fixed PLAUS bounds shared by all
datasets (MinMaxNormalizer.fit() is a no-op; tests/test_normalizer_bounds.py).

Leak pool capped at source size so leakage % matches the PhysioNet ratio.

    PCL_TEST_MODE=1 python detectors/external/run_external2.py --seeds 5
"""
import argparse
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from detectors.harness import Case, confusion, fmt_matrix
from detectors.checks.check2_pretrain_leakage import (
    LEVELS, analyse, flag_from_relative, run_one)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")


_POOLS = None
_POOL_CACHE = None      # --pool-cache path


def load_pools(verbose=True):
    """(MIMIC samples, eICU samples), loaded once.

    Seed-independent at fraction=1.0. Cached in-process and, with --pool-cache,
    on disk.
    """
    global _POOLS
    if _POOLS is not None:
        return _POOLS

    import pickle
    import time

    if _POOL_CACHE and os.path.exists(_POOL_CACHE):
        t0 = time.time()
        with open(_POOL_CACHE, "rb") as fh:
            _POOLS = pickle.load(fh)
        if verbose:
            print(f"pools loaded from cache {_POOL_CACHE} in "
                  f"{time.time() - t0:.0f}s: MIMIC {len(_POOLS[0])} stays, "
                  f"eICU {len(_POOLS[1])} stays", flush=True)
        return _POOLS

    from config import MIMIC_DIR, EICU_DIR
    from src.data.mimic4 import load_mimic4
    from src.data.eicu import load_eicu
    t0 = time.time()
    src_samples, _ = load_mimic4(MIMIC_DIR, fraction=1.0, seed=0)
    tgt_samples, _ = load_eicu(EICU_DIR, fraction=1.0, seed=0)
    _POOLS = (src_samples, tgt_samples)
    if verbose:
        print(f"loaded once in {time.time() - t0:.0f}s: "
              f"MIMIC {len(src_samples)} stays, eICU {len(tgt_samples)} "
              f"stays (reused for every seed)", flush=True)

    if _POOL_CACHE:
        os.makedirs(os.path.dirname(_POOL_CACHE) or ".", exist_ok=True)
        with open(_POOL_CACHE, "wb") as fh:
            pickle.dump(_POOLS, fh, protocol=pickle.HIGHEST_PROTOCOL)
        if verbose:
            print(f"pools cached -> {_POOL_CACHE} "
                  f"({os.path.getsize(_POOL_CACHE) / 1e9:.2f} GB)", flush=True)
    return _POOLS


def build_external(seed, probe_frac=0.25):
    """(source, leak pool, probe). Source is the whole cohort; seed varies target only."""
    from src.data.dataset import ICUDataset

    src_samples, tgt_samples = load_pools()

    rng = np.random.default_rng(seed)
    tgt = [tgt_samples[i] for i in rng.permutation(len(tgt_samples))]

    n_probe = max(50, int(round(probe_frac * len(tgt))))
    probe = tgt[:n_probe]
    # leak pool capped at source size
    pool = tgt[n_probe:n_probe + len(src_samples)]
    return (ICUDataset(src_samples), ICUDataset(pool), ICUDataset(probe))


def measure(seeds, epochs, device, verbose=True):
    results = {frac: [] for frac in LEVELS}
    sizes = None
    for s in range(seeds):
        seed = 42 + s
        src_ds, leak_ds, probe_ds = build_external(seed)
        if sizes is None:
            sizes = (len(src_ds.samples), len(leak_ds.samples),
                     len(probe_ds.samples))
            print(f"source(MIMIC)={sizes[0]}  leak pool(eICU, capped)={sizes[1]}"
                  f"  probe(eICU)={sizes[2]}", flush=True)
        for frac in LEVELS:
            loss, _ = run_one(src_ds, leak_ds, probe_ds, frac, seed, epochs,
                              device)
            results[frac].append(loss)
        if verbose:
            print(f"  seed {seed} done ({s + 1}/{seeds})", flush=True)
    return results, sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--pool-cache", default=None,
                    help="pickle path for the loaded MIMIC/eICU pools; written "
                         "on first run, reused after, so a rerun skips the "
                         "40-60 minute full-scale load")
    args = ap.parse_args()

    global _POOL_CACHE
    _POOL_CACHE = args.pool_cache

    from config import TEST_MODE, D_MODEL, N_LAYERS
    if not TEST_MODE:
        sys.exit("Run with PCL_TEST_MODE=1")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 78)
    print("DETECTOR 2 — external validation, MIMIC-IV -> eICU")
    print("=" * 78)
    print(f"model d={D_MODEL} layers={N_LAYERS} | device={device} | "
          f"{args.seeds} seeds | {args.epochs} epochs")
    print("data path: sample['values'] (fixed PLAUS bounds, shared across "
          "datasets) — see module docstring", flush=True)

    results, sizes = measure(args.seeds, args.epochs, device)
    detected, stats = analyse(results)

    print()
    for frac in LEVELS:
        losses = results[frac]
        print(f"  leakage {int(frac * 100):>3}%  probe loss {np.mean(losses):.6f}"
              f" +/- {np.std(losses, ddof=1) if len(losses) > 1 else 0:.6f}"
              f"   {[round(x, 5) for x in losses]}")

    print(f"\n{'leakage':>9}{'probe loss':>13}{'paired rel. delta':>20}"
          f"{'t':>8}{'agree':>8}{'detected':>10}")
    for frac in LEVELS:
        st = stats[frac]
        print(f"{int(frac * 100):>8}%{st['mean_loss']:>13.6f}"
              f"{st['rel_delta'] * 100:>19.1f}%{st['t']:>8.2f}"
              f"{str(st['sign_agree']):>8}{str(detected[frac]):>10}"
              f"   (crit {-st['crit']:.3f})")

    cases = [Case(f"leakage {int(f * 100)}%", detected[f], bool(f > 0), stats[f])
             for f in LEVELS]
    counts = confusion(cases)
    floor = next((f for f in LEVELS if f > 0 and detected[f]), None)

    print("\n" + "-" * 78)
    print(f"false positive at 0% leakage: {detected[0.0]}   (must be False)")
    print(f"detection floor: "
          f"{f'{int(floor * 100)}% leakage' if floor else 'NOT DETECTED at any level'}")
    print(fmt_matrix("check2 EXTERNAL", counts))
    print(f"\nNOTE: the MIMIC source is the entire cohort ({sizes[0]} stays) at "
          "every seed, so "
          "the source contributes no split variance; only the eICU target split "
          "varies with the seed.")

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "external2.json"), "w", encoding="utf-8") as fh:
        json.dump({"counts": counts,
                   "sizes": {"source": sizes[0], "leak_pool": sizes[1],
                             "probe": sizes[2]},
                   "losses": {str(k): v for k, v in results.items()},
                   "stats": {str(k): v for k, v in stats.items()},
                   "floor": floor}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
