"""Task 4c reporting under both NaN conventions (PREREG_R1_ADDENDUM_2.md, section A).

Reads rebuttal/results/task4c_labels.json; changes no label.

  narrow  divergence-only NaN is outside supported use (the reading applied while labelling)
  broad   a site tagged divergence_only that was labelled UNREACHABLE or GUARDED counts as positive

    python rebuttal/scripts/task4c_report.py
"""
import os
import json
import math

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L = json.load(open(os.path.join(ROOT, "rebuttal", "results", "task4c_labels.json")))
R = "REACHABLE_UNGUARDED"


def cp(k, n, a=0.05):
    """Exact Clopper-Pearson interval by bisection on the binomial CDF."""
    def cdf(x, p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, x + 1))
    lo = 0.0 if k == 0 else _bisect(lambda p: 1 - cdf(k - 1, p) - a / 2)
    hi = 1.0 if k == n else _bisect(lambda p: cdf(k, p) - a / 2, decreasing=True)
    return lo, hi


def _bisect(f, decreasing=False):
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        v = f(mid)
        if (v < 0) == (not decreasing):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fisher_two_sided(a, b, c, d):
    """Exact two-sided p for [[a, b], [c, d]] (sum of tables no more probable than observed)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    pr = lambda x: math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    obs = pr(a)
    return sum(pr(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1) if pr(x) <= obs * (1 + 1e-9))


app = [o for o in L if o["label"] != "NOT_APPLICABLE"]
pos = {"narrow": lambda o: o["label"] == R,
       "broad": lambda o: o["label"] == R or (o["divergence_only"] and o["label"] in ("UNREACHABLE", "GUARDED"))}
out = {"n_sites": len(L), "n_applicable": len(app), "convention_note":
       "The convention was not fixed in advance; both readings are reported and neither is chosen after the fact.",
       "positives_narrow": [], "readings": {}}
for o in app:
    if pos["narrow"](o):
        out["positives_narrow"].append({k: o[k] for k in ("repo", "file", "start", "end", "sha", "kind", "note")})
for name, f in pos.items():
    tot = sum(f(o) for o in app)
    V = [o for o in app if o["kind"] == "V"]; O = [o for o in app if o["kind"] == "O"]
    kv, ko = sum(f(o) for o in V), sum(f(o) for o in O)
    out["readings"][name] = {
        "overall": {"k": tot, "n": len(app), "rate": tot / len(app), "cp95": cp(tot, len(app))},
        "verdict_selection": {"k": kv, "n": len(V), "rate": kv / len(V), "cp95": cp(kv, len(V))},
        "other": {"k": ko, "n": len(O), "rate": ko / len(O), "cp95": cp(ko, len(O))},
        "fisher_two_sided_p_V_vs_O": fisher_two_sided(kv, len(V) - kv, ko, len(O) - ko)}
os.makedirs(os.path.join(ROOT, "rebuttal", "results"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "rebuttal", "results", "task4c_report.json"), "w"), indent=1)
for p in out["positives_narrow"]:
    print(f"POSITIVE {p['repo']} {p['file']}:{p['start']}-{p['end']} @{p['sha']} [{p['kind']}]")
for name, r in out["readings"].items():
    print(name, {k: (v if k.startswith("fisher") else f"{v['k']}/{v['n']} cp95 [{v['cp95'][0]:.3f}, {v['cp95'][1]:.3f}]") for k, v in r.items()})
try:
    from scipy.stats import fisher_exact
    for name, r in out["readings"].items():
        t = [[r["verdict_selection"]["k"], r["verdict_selection"]["n"] - r["verdict_selection"]["k"]],
             [r["other"]["k"], r["other"]["n"] - r["other"]["k"]]]
        print("scipy check", name, fisher_exact(t)[1])
except ImportError:
    print("scipy not installed; own implementation only")
