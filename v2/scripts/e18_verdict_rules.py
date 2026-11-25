"""E18 (PREREG_V2_ADDENDUM_10.md): verdict rules for a 500-stay audit of detector 1, and prevalence.

    python -W ignore v2/scripts/e18_verdict_rules.py --cache DIR   ->  v2/results/e18_verdict_rules.json

DIR is the E8 cache (per-stay labels for ten operationalizations of Sepsis-3 on both databases); it is patient-level and stays outside the repository.
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import numpy as np
from e8_family import assemble, VARIANTS

TAU, N_AUDIT, DRAWS = 0.60, 500, 2000
SEEDS = {"mimic": 20261127, "eicu": 20261128}
PRIMARY = (VARIANTS.index((0, 0)), VARIANTS.index((48, 24)))  # single-point against the reference window [-48,+24]
PAIRS = [(i, j) for i in range(len(VARIANTS)) for j in range(i + 1, len(VARIANTS))]


def kappa_from_counts(n11, p_i, p_j, n):
    """Cohen's kappa for binary labelings from the 2x2 counts, with the shipped convention kappa = 1 when chance agreement is 1."""
    n00 = n - p_i - p_j + n11
    po = (n11 + n00) / n
    pe = (p_i * p_j + (n - p_i) * (n - p_j)) / n ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        k = np.where(pe >= 1.0, 1.0, (po - pe) / (1.0 - pe))
    return k, po, pe


def pair_stats(A):
    """A: (draws, variants, n) int8. Returns kappa, po, pe arrays of shape (draws, variants, variants)."""
    n = A.shape[2]
    Af = A.astype(np.float32)
    n11 = np.einsum("dik,djk->dij", Af, Af)
    p = Af.sum(2)
    return kappa_from_counts(n11, p[:, :, None], p[:, None, :], n)


def rules(k, po, pe, n):
    se = np.sqrt(np.maximum(po * (1 - po), 0.0) / (n * np.maximum((1 - pe) ** 2, 1e-12)))
    point = np.where(k < TAU, 1, 0)  # 1 flag, 0 clear
    interval = np.where(k + 1.96 * se < TAU, 1, np.where(k - 1.96 * se > TAU, 0, -1))  # -1 inconclusive
    return point, interval, se


def boot_flag_prob(a, b, rng, B=400):
    n = len(a)
    idx = rng.integers(0, n, size=(B, n))
    x, y = a[idx].astype(np.float32), b[idx].astype(np.float32)
    n11 = (x * y).sum(1)
    k, _, _ = kappa_from_counts(n11, x.sum(1), y.sum(1), n)
    return float((k < TAU).mean()), np.percentile(k, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    out = {"tau": TAU, "n_audit": N_AUDIT, "draws": DRAWS, "seeds": SEEDS, "primary": [list(VARIANTS[PRIMARY[0]]), list(VARIANTS[PRIMARY[1]])], "sites": {}}
    combos = []  # per (site, pair) rows
    prim = {}
    for site in ("mimic", "eicu"):
        ids, L = assemble(a.cache, site)
        N = L.shape[1]
        rng = np.random.default_rng(SEEDS[site])
        idx = np.stack([rng.choice(N, size=N_AUDIT, replace=False) for _ in range(DRAWS)])
        A = L[:, idx].transpose(1, 0, 2)  # (draws, variants, n)
        k, po, pe = pair_stats(A)
        point, interval, se = rules(k, po, pe, N_AUDIT)
        # whole cohort
        Lf = L.astype(np.float32)
        kc, poc, pec = kappa_from_counts(Lf @ Lf.T, Lf.sum(1)[:, None], Lf.sum(1)[None, :], N)
        for (i, j) in PAIRS:
            theta = float(kc[i, j])
            sd = float(k[:, i, j].std(ddof=1))
            truth = 1 if theta < TAU else 0
            m = abs(TAU - theta) / sd if sd > 0 else float("inf")
            pr, iv = point[:, i, j], interval[:, i, j]
            combos.append({"site": site, "pair": [list(VARIANTS[i]), list(VARIANTS[j])], "theta": theta, "sigma500": sd, "margin": m,
                           "truth_flag": truth, "flag_rate_point": float(pr.mean()),
                           "point_match": float((pr == truth).mean()),
                           "interval_match": float((iv == truth).mean()), "interval_inconclusive": float((iv == -1).mean()),
                           "interval_wrong": float(((iv != -1) & (iv != truth)).mean())})
        # primary control
        i, j = PRIMARY
        if site == "mimic":
            prim["mimic_audit_k"] = k[:, i, j]
        pi, pj = float(L[i].mean()), float(L[j].mean())
        po_c = float(poc[i, j])
        out["sites"][site] = {"cohort": int(N), "primary": {"theta": float(kc[i, j]), "positive_share_single_point": pi, "positive_share_window_48_24": pj,
                                                            "observed_agreement": po_c, "kappa": float(kc[i, j]), "pabak": float(2 * po_c - 1)}}
        if site == "mimic":
            # check the analytic interval against a bootstrap, on 100 audits
            rb = np.random.default_rng(20261129)
            agree, cover_a, cover_b, nb = 0, 0, 0, 100
            for d in range(nb):
                a_, b_ = A[d, i], A[d, j]
                fp, ci = boot_flag_prob(a_, b_, rb)
                lo, hi = k[d, i, j] - 1.96 * se[d, i, j], k[d, i, j] + 1.96 * se[d, i, j]
                cover_a += lo <= kc[i, j] <= hi
                cover_b += ci[0] <= kc[i, j] <= ci[1]
                boot_v = 1 if ci[1] < TAU else (0 if ci[0] > TAU else -1)
                agree += boot_v == interval[d, i, j]
            out["interval_vs_bootstrap_primary"] = {"audits": nb, "analytic_coverage_of_cohort_kappa": cover_a / nb, "bootstrap_coverage": cover_b / nb,
                                                    "verdict_agreement": agree / nb}
            # zone rule on the primary and the five smallest-margin pairs among the other MIMIC combinations
            mim = [c for c in combos if c["site"] == "mimic"]
            order = sorted([c for c in mim if [tuple(c["pair"][0]), tuple(c["pair"][1])] != [VARIANTS[i], VARIANTS[j]] and
                            sorted([tuple(c["pair"][0]), tuple(c["pair"][1])]) != sorted([VARIANTS[i], VARIANTS[j]])], key=lambda c: c["margin"])[:5]
            targets = [(i, j)] + [(VARIANTS.index(tuple(c["pair"][0])), VARIANTS.index(tuple(c["pair"][1]))) for c in order]
            zone = []
            rz = np.random.default_rng(20261130)
            for (u, v) in targets:
                th = float(kc[u, v])
                inc = dec_wrong = match = 0
                for d in range(200):
                    fp, _ = boot_flag_prob(A[d, u], A[d, v], rz)
                    if 0.05 <= fp <= 0.95:
                        inc += 1
                    else:
                        verdict = 1 if fp > 0.95 else 0
                        match += verdict == (1 if th < TAU else 0)
                        dec_wrong += verdict != (1 if th < TAU else 0)
                zone.append({"pair": [list(VARIANTS[u]), list(VARIANTS[v])], "theta": th, "inconclusive": inc / 200, "decisive_wrong": dec_wrong / 200, "decisive_match": match / 200})
            out["zone_rule"] = zone
            # sizes at which the interval rule becomes decisive for the primary control
            sizes = [500, 1000, 2000, 5000, 10000, 20000, 40000, 62500]
            rs = np.random.default_rng(20261131)
            sz = []
            for n_ in sizes:
                reps = 400 if n_ <= 20000 else 100
                dec = wrong = 0
                for _ in range(reps):
                    sel = rs.choice(N, size=n_, replace=False)
                    x, y = L[i, sel].astype(np.float32), L[j, sel].astype(np.float32)
                    kk, pp, ee = kappa_from_counts(float((x * y).sum()), float(x.sum()), float(y.sum()), n_)
                    _, ivv, _ = rules(np.array(kk), np.array(pp), np.array(ee), n_)
                    ivv = int(ivv)
                    dec += ivv != -1
                    wrong += (ivv != -1) and (ivv != (1 if kc[i, j] < TAU else 0))
                sz.append({"n": n_, "reps": reps, "decisive": dec / reps, "decisive_wrong": wrong / reps})
            out["interval_rule_by_size_primary"] = sz
    # group the combinations by margin
    def grp(c):
        return "m<=1.64" if c["margin"] <= 1.64 else ("1.64<m<=3" if c["margin"] <= 3 else "m>3")
    groups = {}
    for c in combos:
        g = groups.setdefault(grp(c), {"combos": 0, "point_match": 0.0, "interval_match": 0.0, "interval_inconclusive": 0.0, "interval_wrong": 0.0})
        g["combos"] += 1
        for key in ("point_match", "interval_match", "interval_inconclusive", "interval_wrong"):
            g[key] += c[key]
    for g in groups.values():
        for key in ("point_match", "interval_match", "interval_inconclusive", "interval_wrong"):
            g[key] = g[key] / g["combos"]
    out["by_margin_group"] = groups
    prim_row = [c for c in combos if c["site"] == "mimic" and {tuple(c["pair"][0]), tuple(c["pair"][1])} == {VARIANTS[PRIMARY[0]], VARIANTS[PRIMARY[1]]}]
    out["primary_row"] = prim_row
    out["combos"] = combos
    path = os.path.join(ROOT, "v2", "results", "e18_verdict_rules.json")
    json.dump(out, open(path, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "combos"}, indent=1))


if __name__ == "__main__":
    main()
