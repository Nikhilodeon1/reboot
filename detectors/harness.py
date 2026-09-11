"""Shared result types and scoring for the confound detectors."""
from collections import namedtuple

Case = namedtuple("Case", "name flagged expected stats")


def confusion(cases):
    """TP/FP/FN/TN counts over Case records."""
    c = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for x in cases:
        if x.flagged and x.expected:
            c["TP"] += 1
        elif x.flagged and not x.expected:
            c["FP"] += 1
        elif not x.flagged and x.expected:
            c["FN"] += 1
        else:
            c["TN"] += 1
    return c


def rates(counts):
    """Precision, recall, FPR. Undefined ratios are nan, not 0."""
    tp, fp, fn, tn = counts["TP"], counts["FP"], counts["FN"], counts["TN"]
    nan = float("nan")
    return {
        "precision": tp / (tp + fp) if (tp + fp) else nan,
        "recall": tp / (tp + fn) if (tp + fn) else nan,
        "fpr": fp / (fp + tn) if (fp + tn) else nan,
    }


def seed_sweep(run_fn, seeds):
    """Per-case flag rate across seeds.

    Raises if the case set or any case's ground truth changes between seeds.
    """
    acc, expected, names0 = {}, {}, None
    for s in seeds:
        cases = run_fn(s)
        names = {c.name for c in cases}
        if names0 is None:
            names0 = names
        elif names != names0:
            raise ValueError(f"case set changed at seed {s}: {names ^ names0}")
        for c in cases:
            if c.name in expected and expected[c.name] != bool(c.expected):
                raise ValueError(
                    f"ground truth for {c.name!r} changed at seed {s}")
            acc.setdefault(c.name, []).append(bool(c.flagged))
            expected[c.name] = bool(c.expected)
    return {n: {"flags": v,
                "n": len(v),
                "flag_rate": sum(v) / len(v),
                "expected": expected[n]}
            for n, v in acc.items()}


# Stochastic detectors report uncertainty with every verdict.
# 3 and 4 are deterministic static analysis; no CI.
STOCHASTIC_CHECKS = {1, 2, 5}
DETERMINISTIC_CHECKS = {3, 4}


def requires_uncertainty(check_number):
    """True for stochastic detectors. Raises on unclassified checks."""
    if check_number in DETERMINISTIC_CHECKS:
        return False
    if check_number in STOCHASTIC_CHECKS:
        return True
    raise ValueError(f"unknown check {check_number!r}: classify it as "
                     "stochastic or deterministic before reporting it")


def fmt_uncertainty(check_number, stats):
    """Uncertainty cell for a results row. Renders MISSING, never blank."""
    if not requires_uncertainty(check_number):
        return "deterministic (no CI: static analysis)"
    if stats is None:
        return "MISSING — stochastic detector reported no uncertainty"
    if "ci_lo" in stats and "ci_hi" in stats:
        s = f"95% CI [{stats['ci_lo']:.3f}, {stats['ci_hi']:.3f}]"
        if stats.get("p_would_flag") is not None:
            s += f", P(flag)={stats['p_would_flag']:.3f}"
        return s
    if "flag_rate" in stats and "n" in stats:
        return f"flagged {int(round(stats['flag_rate'] * stats['n']))}/{stats['n']} seeds"
    if "mean" in stats and "sd" in stats:
        return f"{stats['mean']:.3f} +/- {stats['sd']:.3f}"
    # paired t: within-seed spread
    if "t" in stats and "crit" in stats:
        s = f"paired t={stats['t']:.2f} vs crit {stats['crit']:.3f}"
        if stats.get("floor") is not None:
            s += f" at the {int(stats['floor'] * 100)}% detection floor"
        if stats.get("sign_agree_n") is not None and stats.get("n") is not None:
            s += (f", sign-consistent {stats['sign_agree_n']}/{stats['n']} "
                  "seeds")
        return s
    return "MISSING — stochastic detector reported no uncertainty"


def fmt_matrix(label, counts):
    r = rates(counts)
    return (f"{label:<28}TP={counts['TP']:<3}FP={counts['FP']:<3}"
            f"FN={counts['FN']:<3}TN={counts['TN']:<3}"
            f"prec={r['precision']:.2f} rec={r['recall']:.2f} "
            f"fpr={r['fpr']:.2f}")
