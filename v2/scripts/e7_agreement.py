"""E7 / E7a (PREREG_V2_ADDENDUM_2.md): agreement between a second rater and the labels committed before the detector ran.

    python v2/scripts/e7_agreement.py --sheet 3b --rater <rater json> [--out DIR]
    python v2/scripts/e7_agreement.py --sheet 4c --rater <rater json> [--out DIR]

Reads the committed labels (round 1) and the neutral key of the blind sheet. Writes aggregates only.
"""
import os
import sys
import json
import argparse
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stats_util import clopper_pearson

R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")
E7 = os.environ.get("E7_DIR", r"C:\Users\nikhi\Codes\RES\work_reboot\e7")


def kappa(a, b):
    n = len(a)
    cats = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = collections.Counter(a), collections.Counter(b)
    pe = sum(pa[c] * pb[c] for c in cats) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def load(sheet, rater_path):
    key = json.load(open(os.path.join(E7, f"rater_key_{sheet}.json")))
    lab = json.load(open(os.path.join(R1, "task3b_labels.json" if sheet == "3b" else "task4c_labels.json")))
    by = {(x["repo"], x["file"], x["start"], x["end"]): x for x in lab}
    rater = {r["site"]: r for r in json.load(open(rater_path))}
    rows = []
    for k in key:
        c = by[(k["repo"], k["file"], k["start"], k["end"])]
        r = rater.get(k["site"])
        rows.append((k, c, r))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", choices=["3b", "4c"], required=True)
    ap.add_argument("--rater", required=True)
    ap.add_argument("--out", default=os.path.join(V2, "results"))
    a = ap.parse_args()
    rows = load(a.sheet, a.rater)
    missing = [k["site"] for k, c, r in rows if r is None]
    rows = [(k, c, r) for k, c, r in rows if r is not None]
    res = {"sheet": a.sheet, "sites": len(rows), "missing_from_rater": missing}
    if a.sheet == "3b":
        mine = [c["label"] for k, c, r in rows]
        theirs = [r["label"] for k, c, r in rows]
        real = lambda L: sum(x in ("SOUND", "DISCLOSED_ORACLE", "AMBIGUOUS", "CONTAMINATED") for x in L)
        res["counts_committed"] = dict(collections.Counter(mine))
        res["counts_rater"] = dict(collections.Counter(theirs))
        res["sensitivity"] = {"committed": {"contaminated": sum(x == "CONTAMINATED" for x in mine), "real_selection_sites": real(mine)},
                              "rater": {"contaminated": sum(x == "CONTAMINATED" for x in theirs), "real_selection_sites": real(theirs)}}
        for who, L in (("committed", mine), ("rater", theirs)):
            k_, n_ = res["sensitivity"][who]["contaminated"], res["sensitivity"][who]["real_selection_sites"]
            res["sensitivity"][who]["cp95_contaminated_of_real"] = clopper_pearson(k_, n_)
    else:
        def cls_committed(c):
            if c.get("divergence_only"):
                return "RU_diverged"
            return "RU_ordinary" if c["label"] == "REACHABLE_UNGUARDED" else c["label"]

        def cls_rater(r):
            if r["label"] == "REACHABLE_UNGUARDED":
                return "RU_diverged" if str(r.get("diverged_only")).startswith("diverged") else "RU_ordinary"
            return r["label"]
        mine = [cls_committed(c) for k, c, r in rows]
        theirs = [cls_rater(r) for k, c, r in rows]
        collapse = lambda x: "REACHABLE_UNGUARDED" if x.startswith("RU_") else x
        res["agreement_collapsed_4_class"] = None
        m4, t4 = [collapse(x) for x in mine], [collapse(x) for x in theirs]
        k4 = sum(x == y for x, y in zip(m4, t4))
        res["agreement_collapsed_4_class"] = {"agree": k4, "n": len(m4), "cp95": clopper_pearson(k4, len(m4)), "kappa": kappa(m4, t4)}
        for who, L in (("committed", mine), ("rater", theirs)):
            app = sum(x != "NOT_APPLICABLE" for x in L)
            narrow = sum(x == "RU_ordinary" for x in L)
            broad = sum(x.startswith("RU_") for x in L)
            res.setdefault("sensitivity", {})[who] = {"applicable": app, "narrow": [narrow, app, clopper_pearson(narrow, app)],
                                                       "broad": [broad, app, clopper_pearson(broad, app)]}
    n = len(rows)
    ag = sum(x == y for x, y in zip(mine, theirs))
    res["agreement"] = {"agree": ag, "n": n, "cp95": clopper_pearson(ag, n), "kappa": kappa(mine, theirs)}
    conf = collections.Counter(zip(mine, theirs))
    res["confusion"] = [{"committed": a_, "rater": b_, "n": v} for (a_, b_), v in sorted(conf.items())]
    res["disagreements"] = [{"site": k["site"], "repo": k["repo"], "file": k["file"], "lines": [k["start"], k["end"]], "committed": m_, "rater": t_,
                             "rater_note": r.get("note")} for (k, c, r), m_, t_ in zip(rows, mine, theirs) if m_ != t_]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"e7a_agreement_{a.sheet}.json")
    json.dump(res, open(path, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("confusion", "disagreements")}, indent=1))
    print(len(res["disagreements"]), "disagreements; wrote", path)


if __name__ == "__main__":
    main()
