"""E7a (PREREG_V2_ADDENDUM_2B.md): agreement of several language-model raters with the committed labels and with each other.

    python v2/scripts/e7_combine.py --sheet 3b --rater claude_subagent=<json> --rater claude=<json> --rater gemini=<json> --rater chatgpt=<json>

Per rater: raw agreement with an exact interval and Cohen's kappa against the committed labels. Also: kappa for every pair of raters, the
majority label of the raters that are not the in-session subagent (ties go to AMBIGUOUS or NOT_APPLICABLE), and the median kappa across all raters,
which is the quantity the registered reading rule uses. Writes aggregates only.
"""
import os
import sys
import json
import argparse
import statistics
import itertools
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e7_agreement as A
from stats_util import clopper_pearson


def classes(sheet, path):
    rows = A.load(sheet, path)
    mine, theirs = [], []
    for k, c, r in rows:
        if sheet == "3b":
            mine.append(c["label"])
            theirs.append(r["label"] if r else None)
        else:
            mine.append("RU_diverged" if c.get("divergence_only") else ("RU_ordinary" if c["label"] == "REACHABLE_UNGUARDED" else c["label"]))
            if r is None:
                theirs.append(None)
            elif r["label"] == "REACHABLE_UNGUARDED":
                theirs.append("RU_diverged" if str(r.get("diverged_only")).startswith("diverged") else "RU_ordinary")
            else:
                theirs.append(r["label"])
    return [k["site"] for k, c, r in rows], mine, theirs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", choices=["3b", "4c"], required=True)
    ap.add_argument("--rater", action="append", required=True, help="name=path")
    ap.add_argument("--subagent", default="claude_subagent", help="name of the in-session rater, excluded from the majority vote")
    ap.add_argument("--out", default=os.path.join(A.V2, "results"))
    a = ap.parse_args()
    raters = {}
    mine = sites = None
    for spec in a.rater:
        name, path = spec.split("=", 1)
        sites, mine, theirs = classes(a.sheet, path)
        raters[name] = theirs
    res = {"sheet": a.sheet, "raters": {}, "pairwise_kappa": {}}
    kappas = []
    for name, theirs in raters.items():
        pairs = [(m, t) for m, t in zip(mine, theirs) if t is not None]
        ag = sum(m == t for m, t in pairs)
        kp = A.kappa([m for m, t in pairs], [t for m, t in pairs])
        res["raters"][name] = {"n": len(pairs), "agree": ag, "cp95": clopper_pearson(ag, len(pairs)), "kappa": kp}
        if kp is not None:
            kappas.append(kp)
    for (n1, t1), (n2, t2) in itertools.combinations(raters.items(), 2):
        pr = [(x, y) for x, y in zip(t1, t2) if x is not None and y is not None]
        res["pairwise_kappa"][f"{n1} vs {n2}"] = A.kappa([x for x, y in pr], [y for x, y in pr])
    res["median_kappa_all_raters"] = statistics.median(kappas) if kappas else None
    ext = [t for n, t in raters.items() if n != a.subagent]
    if len(ext) >= 2:
        fallback = "AMBIGUOUS" if a.sheet == "3b" else "NOT_APPLICABLE"
        maj = []
        for i in range(len(mine)):
            votes = collections.Counter(t[i] for t in ext if t[i] is not None)
            top = votes.most_common()
            maj.append(top[0][0] if top and (len(top) == 1 or top[0][1] > top[1][1]) else fallback)
        ag = sum(m == t for m, t in zip(mine, maj))
        res["majority_of_external_raters"] = {"raters": [n for n in raters if n != a.subagent], "agree": ag, "n": len(mine),
                                              "cp95": clopper_pearson(ag, len(mine)), "kappa": A.kappa(mine, maj),
                                              "disagree_sites": [s for s, m, t in zip(sites, mine, maj) if m != t]}
    res["reading"] = ("rubric-dependent: report the range across raters" if res["median_kappa_all_raters"] is not None and res["median_kappa_all_raters"] < 0.6
                      else "stable to the rater: report the agreement")
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, f"e7a_combined_{a.sheet}.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
