"""Task 3c: detector 3 run unchanged on the file of each labelled site.

Shipped vocabulary and the fitted-extended vocabulary as a second column. Files
are parsed with `ast`, never executed. Verdicts are file-level (the detector's
unit); labels are site-level, so a file with several sites appears once per
site and the mismatch is reported, not hidden.

    python -W ignore rebuttal/scripts/task3c_run_detector3.py --root <corpus dir>
"""
import os
import sys
import json
import argparse
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from detectors.checks.check3_selection_audit import audit_file, verdict_for_file, DEFAULT_VOCAB
from detectors.external.run_repos import EXTENDED


def verdict(path, vocab):
    try:
        return verdict_for_file(audit_file(path, vocab))
    except (SyntaxError, ValueError, UnicodeDecodeError, RecursionError):
        return "UNPARSEABLE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(ROOT), "scan_corpus"))
    a = ap.parse_args()
    labels = json.load(open(os.path.join(ROOT, "rebuttal", "results", "task3b_labels.json")))
    cache, rows = {}, []
    for s in labels:
        p = os.path.join(a.root, s["repo"], s["file"])
        if p not in cache:
            cache[p] = (verdict(p, DEFAULT_VOCAB), verdict(p, EXTENDED))
        d, e = cache[p]
        rows.append({"idx": s["idx"], "repo": s["repo"], "file": s["file"], "label": s["label"],
                     "shipped": d, "extended": e})
    table = {}
    for col in ("shipped", "extended"):
        t = {}
        for r in rows:
            t.setdefault(r["label"], Counter())[r[col]] += 1
        table[col] = {k: dict(v) for k, v in t.items()}
    out = {"rows": rows, "table": table, "distinct_files": len(cache),
           "note": "file-level verdicts joined to site-level labels"}
    json.dump(out, open(os.path.join(ROOT, "rebuttal", "results", "task3c_verdicts.json"), "w"), indent=1)
    print(json.dumps(table, indent=1))
    print("distinct files", len(cache))


if __name__ == "__main__":
    main()
