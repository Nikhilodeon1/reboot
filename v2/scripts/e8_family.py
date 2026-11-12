"""E8 stage 2 (PREREG_V2_ADDENDUM_4.md): kappa between every pair of a family of SOFA-window operationalizations of Sepsis-3.

    python -W ignore v2/scripts/e8_family.py label   --cache DIR [--workers 6]         # per-shard labels, resumable
    python -W ignore v2/scripts/e8_family.py analyse --cache DIR --stored labels.npz   # validate against stored labels, then statistics

Scores each variant with the shipped `_sepsis_from_series` (per stay, on the cached components) and uses the shipped `cohens_kappa` and
KAPPA_FLAG. Validation: the variants (48,24), (0,0), (24,12), (72,24) must reproduce the stored full-scale labels exactly. Writes
v2/results/e8_family.json (aggregates only). The cache is patient-level and stays outside the repository.
"""
import os
import sys
import gzip
import json
import pickle
import argparse
import itertools
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import numpy as np

PRES, POSTS = (24, 48, 72), (12, 24, 48)
VARIANTS = [(p, q) for p in PRES for q in POSTS] + [(0, 0)]
STORED = {(48, 24): "SOFA win[-48,+24]", (0, 0): "SOFA single-point", (24, 12): "SOFA win[-24,+12]", (72, 24): "SOFA win[-72,+24]"}
SITES = ("mimic", "eicu")
DRAWS, N_AUDIT = 2000, 500


def shards(cache, site):
    return sorted(f for f in os.listdir(cache) if f.startswith(f"{site}_shard_") and f.endswith(".pkl.gz"))


def label_one(args):
    cache, site, fname = args
    out = os.path.join(cache, "labels", fname.replace(".pkl.gz", ".npz"))
    if os.path.exists(out):
        return fname, "skip"
    from src.data.sofa_sepsis import _sepsis_from_series
    with gzip.open(os.path.join(cache, fname), "rb") as fh:
        d = pickle.load(fh)
    sids = np.array(sorted(d), dtype=np.int64)
    lab = np.zeros((len(sids), len(VARIANTS)), np.int8)
    for i, s in enumerate(sids):
        si_h, C = d[int(s)]
        for j, (pre, post) in enumerate(VARIANTS):
            lab[i, j] = _sepsis_from_series(C, si_h, float(pre), float(post))[0]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp.npz"
    np.savez_compressed(tmp, sids=sids, lab=lab)
    os.replace(tmp, out)
    return fname, "done"


def cmd_label(a):
    jobs = [(a.cache, site, f) for site in SITES for f in shards(a.cache, site)]
    with mp.Pool(a.workers) as pool:
        for fname, st in pool.imap_unordered(label_one, jobs):
            print(fname, st, flush=True)


def assemble(cache, site):
    ids = np.load(os.path.join(cache, f"{site}_ids.npy"))
    pos = {int(s): i for i, s in enumerate(ids)}
    L = np.zeros((len(VARIANTS), len(ids)), np.int8)
    for f in shards(cache, site):
        z = np.load(os.path.join(cache, "labels", f.replace(".pkl.gz", ".npz")))
        idx = np.array([pos[int(s)] for s in z["sids"]])
        L[:, idx] = z["lab"].T
    return ids, L


def clopper_pearson(k, n):
    from stats_util import clopper_pearson as cp
    return [round(x, 3) for x in cp(k, n)]


def cmd_analyse(a):
    from detectors.checks.check1_label_shift import cohens_kappa, KAPPA_FLAG
    from detectors.external.run_external1 import load_labels
    (m_ids, _, m_sofa), (e_ids, _, e_sofa) = load_labels(a.stored)
    stored = {"mimic": (m_ids, m_sofa), "eicu": (e_ids, e_sofa)}
    out = {"threshold": KAPPA_FLAG, "n_audit": N_AUDIT, "draws": DRAWS, "variants": [list(v) for v in VARIANTS], "sites": {}}
    for site in SITES:
        ids, L = assemble(a.cache, site)
        sids, sofa = stored[site]
        if len(sids) != len(ids) or not np.array_equal(sids, ids):
            raise SystemExit(f"VALIDATION FAILED ({site}): cohort ids differ from the stored labels")
        val = {}
        for v, name in STORED.items():
            diff = int((L[VARIANTS.index(v)].astype(int) != np.asarray(sofa[name], int)).sum())
            val[str(v)] = {"stored_variant": name, "stays_differing": diff}
            if diff:
                json.dump({"site": site, "validation": val}, open(os.path.join(a.out, "e8_validation_FAILED.json"), "w"), indent=1)
                raise SystemExit(f"VALIDATION FAILED ({site}) for {v}: {diff} stays differ")
        N = len(ids)
        rng = np.random.default_rng(20260412 + (0 if site == "mimic" else 1))
        draws = [rng.choice(N, size=N_AUDIT, replace=False) for _ in range(DRAWS)]
        pairs = []
        for (i, vi), (j, vj) in itertools.combinations(list(enumerate(VARIANTS)), 2):
            x, y = L[i].astype(int), L[j].astype(int)
            theta = float(cohens_kappa(x, y))
            ks = []
            und = 0
            for idx in draws:
                k = cohens_kappa(x[idx], y[idx])
                if np.isfinite(k):
                    ks.append(k)
                else:
                    und += 1
            ks = np.array(ks)
            sd = float(ks.std(ddof=1)) if len(ks) > 1 else float("nan")
            p_flag = float((ks < KAPPA_FLAG).mean()) if len(ks) else float("nan")
            m = abs(KAPPA_FLAG - theta) / sd if sd and np.isfinite(sd) and sd > 0 else float("inf")
            pairs.append({"a": list(vi), "b": list(vj), "kappa": theta, "audit_sd": sd, "margin_m": m, "p_flag": p_flag,
                          "undecidable_draws": und, "prev_a": float(x.mean()), "prev_b": float(y.mean())})
        ok = [p for p in pairs if p["undecidable_draws"] <= 0.01 * DRAWS]
        k_zone = sum(0.05 <= p["p_flag"] <= 0.95 for p in ok)
        k_m = sum(p["margin_m"] <= 3 for p in ok)
        out["sites"][site] = {"cohort": N, "positives_per_variant": {str(v): int(L[i].sum()) for i, v in enumerate(VARIANTS)},
                              "validation": val, "pairs": pairs, "pairs_decidable": len(ok), "pairs_total": len(pairs),
                              "zone_0.05_0.95": [k_zone, len(ok), clopper_pearson(k_zone, len(ok))],
                              "m_le_3": [k_m, len(ok), clopper_pearson(k_m, len(ok))],
                              "kappa_min_median_max": [float(min(p["kappa"] for p in pairs)), float(np.median([p["kappa"] for p in pairs])),
                                                       float(max(p["kappa"] for p in pairs))]}
        print(site, "zone", out["sites"][site]["zone_0.05_0.95"], "m<=3", out["sites"][site]["m_le_3"], flush=True)
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e8_family.json"), "w"), indent=1)
    print("wrote e8_family.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["label", "analyse"])
    ap.add_argument("--cache", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stored")
    ap.add_argument("--out", default=os.path.join(ROOT, "v2", "results"))
    args = ap.parse_args()
    {"label": cmd_label, "analyse": cmd_analyse}[args.mode](args)
