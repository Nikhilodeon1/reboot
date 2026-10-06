"""Task 1: exact intervals, control margins, Type 2 flag-probability model,
validation-depth matrix. CPU only, no clinical data needed.

Everything here is computed from archived aggregates. Full-scale detector 1
figures were transcribed from run output (the logs were lost); they are marked
provenance=transcribed wherever they appear.

    python rebuttal/scripts/task1_stats.py
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
RES = os.path.join(REPO, "detectors", "results")
OUT_T = os.path.join(HERE, "tables")
OUT_R = os.path.join(HERE, "results")
os.makedirs(OUT_T, exist_ok=True)
os.makedirs(OUT_R, exist_ok=True)

TAU = 0.60          # detector 1 flag threshold
CRIT_T = 2.132      # one-sided 5% critical value at df 4


# ── exact interval helpers ──────────────────────────────────────────────────
def _binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial CI by bisection on the binomial CDF."""
    if n == 0:
        return (float("nan"), float("nan"))
    lo, hi = 0.0, 1.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(200):                      # P(X >= k) = alpha/2
            m = (a + b) / 2
            if 1 - _binom_cdf(k - 1, n, m) < alpha / 2:
                a = m
            else:
                b = m
        lo = (a + b) / 2
    if k < n:
        a, b = 0.0, 1.0
        for _ in range(200):                      # P(X <= k) = alpha/2
            m = (a + b) / 2
            if _binom_cdf(k, n, m) > alpha / 2:
                a = m
            else:
                b = m
        hi = (a + b) / 2
    return (lo, hi)


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - half) / d, (c + half) / d)


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def sd_from_ci(lo, hi):
    """SD implied by a symmetric 95% interval."""
    return (hi - lo) / (2 * 1.959964)


def rows_to_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print("wrote", os.path.relpath(path, REPO))


def load(name):
    with open(os.path.join(RES, name), encoding="utf-8") as fh:
        return json.load(fh)


# ── 1a. Clopper-Pearson for every confusion headline ────────────────────────
CONFUSION = {
    "detector 1 (internal)": (1, 0, 0, 1, "demo eICU"),
    "detector 2 (internal)": (3, 0, 0, 1, "demo PhysioNet A->B 900/site"),
    "detector 3 (internal)": (1, 0, 0, 1, "code fixtures"),
    "detector 4 (internal)": (1, 0, 0, 8, "code, 9 pairs"),
    "detector 5 (internal)": (0, 0, 1, 1, "demo PhysioNet 1200/arm"),
    "pooled (reference only, heterogeneous cases)": (6, 0, 1, 12, "mixed"),
    "detector 1 external MIMIC": (1, 0, 0, 3, "full MIMIC-IV, transcribed"),
    "detector 1 external eICU": (1, 0, 0, 3, "full eICU-CRD, transcribed"),
    "detector 2 external full": (3, 0, 0, 1, "full MIMIC-IV->eICU"),
}


def task_1a():
    rows = []
    for name, (tp, fp, fn, tn, scale) in CONFUSION.items():
        for metric, k, n in (("precision", tp, tp + fp),
                             ("recall", tp, tp + fn),
                             ("FPR", fp, fp + tn)):
            if n == 0:
                rows.append([name, scale, metric, "undefined", 0, "MISSING",
                             "MISSING"])
                continue
            lo, hi = clopper_pearson(k, n)
            rows.append([name, scale, metric, f"{k/n:.3f}", n,
                         f"{lo:.3f}", f"{hi:.3f}"])
    rows_to_csv(os.path.join(OUT_T, "task1a_exact_intervals.csv"),
                ["case", "scale", "metric", "point", "n", "ci_lo", "ci_hi"], rows)
    return rows


# ── 1c. Type 2 flag-probability model ───────────────────────────────────────
# Full-scale detector 1 figures, transcribed from run output (logs lost).
FULL = {
    "MIMIC ctrl win vs single-point": dict(n=74829, kappa=0.602, coh=(0.597, 0.607),
                                           aud=(0.539, 0.663), p_obs=0.484),
    "MIMIC ctrl win[-24,+12]":        dict(n=74829, kappa=0.913, coh=(0.910, 0.916),
                                           aud=(0.876, 0.948), p_obs=0.000),
    "MIMIC ctrl win[-72,+24]":        dict(n=74829, kappa=0.993, coh=(0.992, 0.994),
                                           aud=(0.980, 1.000), p_obs=0.000),
    "MIMIC POSITIVE ICD vs SOFA":     dict(n=74829, kappa=0.174, coh=(0.168, 0.179),
                                           aud=(0.104, 0.243), p_obs=1.000),
    "eICU ctrl win vs single-point":  dict(n=132900, kappa=0.826, coh=(0.821, 0.831),
                                           aud=(0.737, 0.901), p_obs=0.000),
    "eICU ctrl win[-24,+12]":         dict(n=132900, kappa=0.986, coh=(0.984, 0.987),
                                           aud=(0.959, 1.000), p_obs=0.000),
    "eICU ctrl win[-72,+24]":         dict(n=132900, kappa=1.000, coh=(1.000, 1.000),
                                           aud=(1.000, 1.000), p_obs=0.000),
    "eICU POSITIVE ICD vs SOFA":      dict(n=132900, kappa=0.451, coh=(0.444, 0.458),
                                           aud=(0.334, 0.560), p_obs=0.996),
}


def task_1c():
    boot = load("bootstrap_kappa.json")
    rows = []

    # demo, from the archived bootstrap
    for name, v in boot.items():
        sd_coh = sd_from_ci(v["ci_lo"], v["ci_hi"])
        sd_aud = sd_from_ci(v["audit_ci_lo"], v["audit_ci_hi"])
        degenerate = v["audit_n"] >= v["n"]
        pred_coh = phi((TAU - v["kappa"]) / sd_coh) if sd_coh > 0 else (
            1.0 if v["kappa"] <= TAU else 0.0)
        pred_aud = phi((TAU - v["kappa"]) / sd_aud) if sd_aud > 0 else (
            1.0 if v["kappa"] <= TAU else 0.0)
        rows.append(["demo", name, v["n"], v["audit_n"],
                     f"{v['kappa']:.4f}", f"{sd_coh:.5f}", f"{sd_aud:.5f}",
                     f"{pred_coh:.3f}", f"{v['p_would_flag']:.3f}",
                     f"{pred_aud:.3f}", f"{v['audit_p_would_flag']:.4f}",
                     "audit==cohort, no draw variance" if degenerate else "",
                     "archived"])

    # full scale, transcribed
    for name, v in FULL.items():
        sd_coh = sd_from_ci(*v["coh"])
        sd_aud = sd_from_ci(*v["aud"])
        pred_aud = phi((TAU - v["kappa"]) / sd_aud) if sd_aud > 0 else (
            1.0 if v["kappa"] <= TAU else 0.0)
        pred_coh = phi((TAU - v["kappa"]) / sd_coh) if sd_coh > 0 else (
            1.0 if v["kappa"] <= TAU else 0.0)
        rows.append(["full", name, v["n"], 500,
                     f"{v['kappa']:.4f}", f"{sd_coh:.5f}", f"{sd_aud:.5f}",
                     f"{pred_coh:.3f}", "MISSING",
                     f"{pred_aud:.3f}", f"{v['p_obs']:.3f}",
                     "", "transcribed"])

    rows_to_csv(os.path.join(OUT_T, "task1c_flag_probability_model.csv"),
                ["scale", "case", "n_cohort", "n_audit", "kappa",
                 "sd_cohort", "sd_audit", "pred_P_flag_cohort",
                 "obs_P_flag_cohort", "pred_P_flag_audit", "obs_P_flag_audit",
                 "note", "provenance"], rows)

    # legitimate-variation band: same implementation pair, different databases
    band = []
    for label, (mim, eic) in {
        "win vs single-point": ("MIMIC ctrl win vs single-point",
                                "eICU ctrl win vs single-point"),
        "win[-48,+24] vs win[-24,+12]": ("MIMIC ctrl win[-24,+12]",
                                         "eICU ctrl win[-24,+12]"),
        "win[-48,+24] vs win[-72,+24]": ("MIMIC ctrl win[-72,+24]",
                                         "eICU ctrl win[-72,+24]"),
    }.items():
        band.append([label, f"{FULL[mim[0] if isinstance(mim, tuple) else mim]['kappa']:.3f}",
                     f"{FULL[eic]['kappa']:.3f}",
                     f"{abs(FULL[mim]['kappa'] - FULL[eic]['kappa']):.3f}"])
    rows_to_csv(os.path.join(OUT_T, "task1c_legitimate_variation_band.csv"),
                ["implementation pair", "kappa MIMIC (full)", "kappa eICU (full)",
                 "abs difference"], band)
    return rows


# ── 1b. control margins ─────────────────────────────────────────────────────
def task_1b():
    boot = load("bootstrap_kappa.json")
    c5 = load("check5.json")
    c2r = load("check2_results.json")
    rows = []

    def add(det, control, scale, stat, thr, sd, note, prov):
        native = abs(thr - stat)
        if sd and sd > 0:
            m = native / sd
            cls = "discriminating" if m <= 3 else "ceiling"
            rows.append([det, control, scale, f"{stat:.4f}", f"{thr:.2f}",
                         f"{native:.4f}", f"{sd:.5f}", f"{m:.2f}", cls, note, prov])
        else:
            rows.append([det, control, scale, f"{stat:.4f}", f"{thr:.2f}",
                         f"{native:.4f}", "MISSING", "MISSING", "MISSING",
                         note, prov])

    # detector 1, demo (archived draws)
    for name, v in boot.items():
        if "POSITIVE" in name:
            continue
        sd = sd_from_ci(v["audit_ci_lo"], v["audit_ci_hi"])
        note = "audit==cohort, no draw variance" if v["audit_n"] >= v["n"] else ""
        add("1", name, f"demo n={v['n']}", v["kappa"], TAU, sd, note, "archived")

    # detector 1, full (transcribed CIs)
    for name, v in FULL.items():
        if "POSITIVE" in name:
            continue
        add("1", name, f"full n={v['n']}", v["kappa"], TAU,
            sd_from_ci(*v["aud"]), "SD derived from published audit CI",
            "transcribed")

    # detector 2, 0% false-positive control: decision is on the paired t
    base = c2r["0.0"]
    add("2", "0% leakage control (t vs crit)", "demo 900/site, 5 seeds",
        0.0, CRIT_T, None,
        "flag rule is t <= -2.132 with all-negative signs; t at 0% is 0 by "
        "construction, no archived SD of t", "archived")

    # detector 5 controls
    for case in c5["cases"]:
        if case["expected"]:
            continue
        st = case["stats"]
        add("5", case["name"] + " (composition gate)",
            f"demo n={st.get('n')} stays/arm, 1 seed",
            st["composition_gap_ratio"], 0.30, None,
            "single seed archived, no dispersion", "archived")
        add("5", case["name"] + " (availability gate)",
            f"demo n={st.get('n')} stays/arm, 1 seed",
            st["max_avail_ratio"], 2.00, None,
            "single seed archived, no dispersion", "archived")

    rows_to_csv(os.path.join(OUT_T, "task1b_control_margins.csv"),
                ["detector", "control", "scale", "statistic", "threshold",
                 "native margin", "sd", "m (z units)", "class", "note",
                 "provenance"], rows)
    return rows


# ── 1d. validation-depth matrix ─────────────────────────────────────────────
def task_1d(margin_rows):
    disc = {}
    for r in margin_rows:
        det, cls = r[0], r[8]
        disc.setdefault(det, {"discriminating": 0, "ceiling": 0, "unknown": 0})
        key = cls if cls in ("discriminating", "ceiling") else "unknown"
        disc[det][key] += 1

    spec = {
        "1": dict(pos_int=1, ctrl_int=1, pos_ext=2, ctrl_ext=6,
                  ext_truth="two published Sepsis-3 operationalizations",
                  scale="demo eICU; full MIMIC-IV + eICU-CRD",
                  seeds="1 (verdict); 5000 bootstrap resamples",
                  unc="bootstrap CI + P(flag)", base="Task 5c (pending)",
                  manual="n/a"),
        "2": dict(pos_int=3, ctrl_int=1, pos_ext=3, ctrl_ext=1,
                  ext_truth="controlled injection (dose)",
                  scale="demo PhysioNet 900/site; full MIMIC-IV->eICU",
                  seeds="5", unc="paired t, df 4",
                  base="published (demo, different n) + Task 5a",
                  manual="n/a"),
        "3": dict(pos_int=1, ctrl_int=1, pos_ext=0, ctrl_ext=0,
                  ext_truth="historical defect in own history; 727 third-party files, 0 recognised",
                  scale="code corpus, 18 repos", seeds="-",
                  unc="deterministic", base="Task 3f (Yang et al., pending)",
                  manual="Task 3 (pending)"),
        "4": dict(pos_int=1, ctrl_int=8, pos_ext=0, ctrl_ext=0,
                  ext_truth="no external positive found",
                  scale="code, 9 constraint/loader pairs", seeds="-",
                  unc="deterministic", base="live search (pending)",
                  manual="n/a"),
        "5": dict(pos_int=1, ctrl_int=1, pos_ext=3, ctrl_ext=2,
                  ext_truth="controlled ablation (dose)",
                  scale="demo PhysioNet 1200/arm; external eICU", seeds="5 (external), 1 (internal)",
                  unc="flag rate across seeds", base="out of scope (5e)",
                  manual="n/a"),
    }
    rows = []
    for det, s in spec.items():
        d = disc.get(det, {"discriminating": 0, "ceiling": 0, "unknown": 0})
        rows.append([det, s["pos_int"], s["ctrl_int"], s["pos_ext"], s["ctrl_ext"],
                     d["discriminating"], d["ceiling"], d["unknown"],
                     s["ext_truth"], s["scale"], s["seeds"], s["unc"],
                     s["base"], s["manual"]])
    rows_to_csv(os.path.join(OUT_T, "task1d_validation_depth.csv"),
                ["detector", "positives internal", "controls internal",
                 "positives external", "controls external",
                 "controls discriminating (m<=3)", "controls ceiling (m>3)",
                 "controls margin unknown", "external ground truth", "scale",
                 "seeds", "uncertainty", "baseline coverage",
                 "manual-label coverage"], rows)
    return rows


# ── estimand audit: is the paper's demo->full P(flag) comparison like-for-like?
def estimand_audit():
    boot = load("bootstrap_kappa.json")
    mim = boot["MIMIC SOFA win[-48,+24] vs SOFA single-point"]
    full = FULL["MIMIC ctrl win vs single-point"]
    sd_coh_full = sd_from_ci(*full["coh"])
    out = {
        "paper_sentence": "P(flag) 0.216 at n=117 -> 0.484 at full scale",
        "demo_cohort_bootstrap_P_flag": mim["p_would_flag"],
        "demo_audit_draw_P_flag": mim["audit_p_would_flag"],
        "demo_audit_n": mim["audit_n"],
        "demo_cohort_n": mim["n"],
        "demo_audit_is_degenerate": mim["audit_n"] >= mim["n"],
        "full_audit_draw_P_flag": full["p_obs"],
        "full_cohort_bootstrap_P_flag_predicted":
            round(phi((TAU - full["kappa"]) / sd_coh_full), 3),
        "demo_kappa": mim["kappa"],
        "demo_kappa_ci": [mim["ci_lo"], mim["ci_hi"]],
        "full_kappa": full["kappa"],
        "full_kappa_inside_demo_ci":
            mim["ci_lo"] <= full["kappa"] <= mim["ci_hi"],
        "finding": (
            "0.216 is the COHORT bootstrap P(kappa<=0.60) at n=117; 0.484 is the "
            "AUDIT-DRAW P(flag) at n=74,829. Different estimands. At demo scale "
            "the audit subset IS the whole cohort (min(500,117)=117 drawn without "
            "replacement), so the audit-draw estimand has zero variance and gives "
            "P=0.000. Like-for-like on the cohort bootstrap, full scale is ~0.22, "
            "essentially demo's 0.216. The demo kappa CI also contains the "
            "full-cohort value, so the two estimates are not distinguishable."),
    }
    with open(os.path.join(OUT_R, "task1_estimand_audit.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\n=== ESTIMAND AUDIT ===")
    for k, v in out.items():
        print(f"  {k}: {v}")
    return out


if __name__ == "__main__":
    task_1a()
    task_1c()
    m = task_1b()
    task_1d(m)
    estimand_audit()
