"""Check 5: missingness/scale artifacts in aggregate cross-site scores.

Per-stay aggregate over computable components. Compares the naive gap with a
composition-only gap (pooled component values, so only the active set varies).
Variant A flags on availability skew AND composition_gap_ratio.

composition_gap_ratio is a ratio of two gaps, unbounded above 1. Not a share.

Positive: PhysioNet Site A vs B. Negative: Site A vs itself. Raw PSVs, no model.
"""
import os
import sys

import numpy as np
import pandas as pd


def _physionet_root():
    """PHYSIONET_DIR from config; falls back to repo data/."""
    here = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        from config import PHYSIONET_DIR
        return PHYSIONET_DIR
    except Exception:
        return os.path.join(here, "data", "physionet2019")


ROOT = _physionet_root()

AVAIL_RATIO_FLAG = 2.0     # availability ratio gate
# composition_gap_ratio gate; named COMP_EXPLAINS_FLAG in PREREGISTRATION.md
COMP_GAP_RATIO_FLAG = 0.30
COMP_EXPLAINS_FLAG = COMP_GAP_RATIO_FLAG   # pre-registration alias


# Decision rules, fixed in detectors/PREREGISTRATION.md.
# A: original conjunction. B: drops the composition gate.

def variant_a(stats):
    """Availability skew AND composition gate."""
    return bool(stats["max_avail_ratio"] > AVAIL_RATIO_FLAG
                and stats["composition_gap_ratio"] > COMP_GAP_RATIO_FLAG)


def variant_b(stats):
    """Availability only; composition_gap_ratio reported, not gated."""
    return bool(stats["max_avail_ratio"] > AVAIL_RATIO_FLAG)


VARIANTS = {"A_conjunction": variant_a, "B_availability_only": variant_b}


def components(df):
    """Per-timestep normalized residuals per computable constraint."""
    out = {}
    c = df.columns
    if all(k in c for k in ("SBP", "DBP", "MAP")):
        m = df[["SBP", "DBP", "MAP"]].dropna()
        if len(m):
            out["MAP"] = np.abs((m.MAP - (m.DBP + (m.SBP - m.DBP) / 3.0)) / 180.0).values
    if all(k in c for k in ("pH", "HCO3", "PaCO2")):
        m = df[["pH", "HCO3", "PaCO2"]].dropna()
        m = m[(m.HCO3 > 0) & (m.PaCO2 > 0)]
        if len(m):
            pred = 6.1 + np.log10(m.HCO3 / (0.0307 * m.PaCO2))
            out["HH"] = (((m.pH - pred) / 1.4) ** 2).values
    if "O2Sat" in c and "SaO2" in c:
        m = df[["O2Sat", "SaO2"]].dropna()
        if len(m):
            out["SpO2"] = (((m.O2Sat - m.SaO2) / 50.0) ** 2).values
    return out


def scan(files):
    """Per-stay mean residuals and total timesteps.

    Stay-level: site-level averaging hides the composition effect.
    """
    stays, hours = [], 0
    for path in files:
        df = pd.read_csv(path, sep="|")
        hours += len(df)
        comp = components(df)
        if comp:
            stays.append({k: float(v.mean()) for k, v in comp.items() if len(v)})
    return stays, hours


def run_check(name_a, files_a, name_b, files_b, verbose=True, rule=variant_a):
    """Read PSVs, then run_check_on_stays."""
    A, _ = scan(files_a)
    B, _ = scan(files_b)
    return run_check_on_stays(name_a, A, name_b, B, verbose=verbose, rule=rule,
                              keys=["MAP", "HH", "SpO2"])


def run_check_on_stays(name_a, A, name_b, B, verbose=True, rule=variant_a,
                       keys=("MAP", "HH", "SpO2")):
    """Diagnostic over per-stay {component: residual} dicts. Shared by external runs."""
    keys = list(keys)

    def avail(stays, k):
        return sum(1 for s in stays if k in s) / max(len(stays), 1)

    def comp_mean(stays, k):
        v = [s[k] for s in stays if k in s]
        return float(np.mean(v)) if v else np.nan

    # pooled component means, shared by both sites
    pooled = {}
    for k in keys:
        v = [s[k] for s in A + B if k in s]
        pooled[k] = float(np.mean(v)) if v else np.nan

    def aggregate(stays, use_pooled):
        """Mean over stays of (mean over that stay's ACTIVE components)."""
        out = []
        for st in stays:
            vals = [pooled[k] if use_pooled else st[k] for k in keys if k in st]
            if vals:
                out.append(float(np.mean(vals)))
        return float(np.mean(out)) if out else np.nan

    naive = (aggregate(A, False), aggregate(B, False))
    # composition-only: pooled values, only the active set varies
    comp_only = (aggregate(A, True), aggregate(B, True))

    rel = lambda t: abs(t[0] - t[1]) / max(abs(t[0]), abs(t[1]), 1e-12)
    naive_gap, comp_gap = rel(naive), rel(comp_only)
    # ratio of two gaps; unbounded above 1 (1.414 on PhysioNet A vs itself)
    composition_gap_ratio = (comp_gap / naive_gap) if naive_gap > 1e-9 else 0.0

    max_ratio = 0.0
    for k in keys:
        a, b = avail(A, k), avail(B, k)
        if a > 0 and b > 0:
            max_ratio = max(max_ratio, max(a / b, b / a))
        elif a != b:
            max_ratio = float("inf")

    stats = {"max_avail_ratio": float(max_ratio),
             "composition_gap_ratio": float(composition_gap_ratio),
             "naive_gap": float(naive_gap), "comp_gap": float(comp_gap),
             "n_stays_a": len(A), "n_stays_b": len(B)}
    flagged = rule(stats)

    if verbose:
        print(f"")
        print(f"--- {name_a}  vs  {name_b} ---")
        print(f"{'component':<10}{'avail A':>10}{'avail B':>10}{'ratio':>9}"
              f"{'mean A':>11}{'mean B':>11}{'scale':>8}")
        base = pooled[keys[0]]      # scale relative to first term
        for k in keys:
            a, b = avail(A, k), avail(B, k)
            r = max(a, b) / min(a, b) if min(a, b) > 0 else float("inf")
            ma, mb = comp_mean(A, k), comp_mean(B, k)
            print(f"{k:<10}{a:>10.4f}{b:>10.4f}{r:>9.1f}{ma:>11.5f}{mb:>11.5f}"
                  f"{pooled[k]/base:>8.2f}")
        print(f"  aggregate, as scored      : {naive[0]:.5f} vs {naive[1]:.5f}"
              f"   (relative gap {naive_gap:.3f})")
        print(f"  aggregate, composition-only: {comp_only[0]:.5f} vs {comp_only[1]:.5f}"
              f"   (relative gap {comp_gap:.3f})")
        print(f"  max availability ratio {max_ratio:.1f} (flag > {AVAIL_RATIO_FLAG})")
        print(f"  composition/naive gap RATIO (unbounded, not a %): "
              f"{composition_gap_ratio:.2f} (flag > {COMP_GAP_RATIO_FLAG})")
        print(f"  ==> {'FLAGGED: composition artifact' if flagged else 'clean'}")
    return flagged, stats


def sample_files(seed, n, legacy=False):
    """Seeded random stay samples per site.

    legacy=True: alphabetical prefix `sorted(listdir)[:n]` (retracted; not random).
    """
    a_dir = os.path.join(ROOT, "training_setA")
    b_dir = os.path.join(ROOT, "training_setB")
    if not os.path.isdir(a_dir):
        sys.exit(f"missing {a_dir}")
    all_a = [f for f in sorted(os.listdir(a_dir)) if f.endswith(".psv")]
    all_b = [f for f in sorted(os.listdir(b_dir)) if f.endswith(".psv")]
    if legacy:
        ia, ib = range(2 * n), range(n)
    else:
        rng = np.random.default_rng(seed)
        ia = rng.permutation(len(all_a))[:2 * n]
        ib = rng.permutation(len(all_b))[:n]
    return ([os.path.join(a_dir, all_a[i]) for i in ia],
            [os.path.join(b_dir, all_b[i]) for i in ib])


def run(seed=0, n=1200, pair=None, verbose=False, legacy=False):
    """Cross-site positive plus same-site control.

    pair: (name_a, files_a, name_b, files_b, expected) overrides the positive.
    """
    from detectors.harness import Case
    fa, fb = sample_files(seed, n, legacy=legacy)

    if pair is None:
        pos_args = ("PhysioNet Site A", fa[:n], "PhysioNet Site B", fb, True)
    else:
        pos_args = pair
    na, la, nb, lb, exp = pos_args
    pos, pos_stats = run_check(na, la, nb, lb, verbose=verbose)

    # negative control: Site A halves
    half = len(fa) // 2
    neg, neg_stats = run_check(f"{na} (half 1)", fa[:half],
                               f"{na} (half 2)", fa[half:], verbose=verbose)

    return [Case(f"positive ({na} vs {nb})", bool(pos), bool(exp),
                 dict(pos_stats, seed=seed, n=n)),
            Case(f"negative ({na} vs itself)", bool(neg), False,
                 dict(neg_stats, seed=seed, n=n))]


def main():
    from detectors.harness import confusion, fmt_matrix
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print("=" * 78)
    print("CHECK 5 — missingness/scale artifacts in aggregate cross-site scores")
    print("=" * 78)
    print(f"(sampling {n} stays per arm, seed={seed})")

    cases = run(seed=seed, n=n, verbose=True)

    print("\n" + "-" * 78)
    for c in cases:
        print(f"{c.name:<40} flagged={str(c.flagged):<6} "
              f"expected={str(c.expected)}")
    counts = confusion(cases)
    print("\n" + fmt_matrix("check5", counts))
    print("verdict:", "DETECTOR VALIDATED"
          if counts["FP"] == 0 and counts["FN"] == 0 else "NEEDS WORK")


if __name__ == "__main__":
    main()
