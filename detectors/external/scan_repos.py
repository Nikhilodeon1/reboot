"""Detector 3 recognition rate across the scan corpus.

Measures whether a sweep is recognised at all, not per-file ground truth.
Unparseable files counted separately, never as clean.

    python detectors/external/scan_repos.py --root <repos dir>
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from detectors.checks.check3_selection_audit import audit_file, verdict_for_file
from detectors.external.run_repos import EXTENDED

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")


def scan(root, vocab, label):
    per_repo, tot = {}, {"files": 0, "parsed": 0, "unparseable": 0,
                         "recognised": 0, "contaminated": 0, "ok": 0}
    for repo in sorted(os.listdir(root)):
        rp = os.path.join(root, repo)
        if not os.path.isdir(rp):
            continue
        row = {"files": 0, "parsed": 0, "unparseable": 0, "recognised": 0,
               "contaminated": 0, "ok": 0, "hits": []}
        for dirpath, dirnames, filenames in os.walk(rp):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                row["files"] += 1
                try:
                    res = audit_file(path, vocab)
                except (SyntaxError, ValueError, UnicodeDecodeError):
                    row["unparseable"] += 1
                    continue
                row["parsed"] += 1
                verdict = verdict_for_file(res)
                if verdict in ("CONTAMINATED", "OK"):
                    row["recognised"] += 1
                    row["contaminated"] += (verdict == "CONTAMINATED")
                    row["ok"] += (verdict == "OK")
                    row["hits"].append({
                        "file": os.path.relpath(path, root),
                        "verdict": verdict,
                        "sweeps": [r["function"] for r in res]})
        per_repo[repo] = row
        for k in tot:
            tot[k] += row[k]
    print(f"\n{'=' * 74}\n{label}\n{'=' * 74}")
    print(f"{'repo':<32}{'files':>7}{'parsed':>8}{'unparse':>9}{'recognised':>12}")
    for repo, r in per_repo.items():
        print(f"{repo:<32}{r['files']:>7}{r['parsed']:>8}"
              f"{r['unparseable']:>9}{r['recognised']:>12}")
    print(f"{'TOTAL':<32}{tot['files']:>7}{tot['parsed']:>8}"
          f"{tot['unparseable']:>9}{tot['recognised']:>12}")
    return per_repo, tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    pre_repo, pre_tot = scan(args.root, None, "PRE-EXTENSION (detector as written)")
    post_repo, post_tot = scan(args.root, EXTENDED,
                               "POST-EXTENSION (vocabulary FITTED to these repos)")

    print(f"\n{'=' * 74}\nOUTCOME\n{'=' * 74}")
    print(f"python files scanned : {pre_tot['files']}")
    print(f"parsed successfully  : {pre_tot['parsed']}")
    print(f"failed to parse      : {pre_tot['unparseable']} "
          f"(counted separately, never as clean)")
    print(f"sweep recognised, pre-extension  : {pre_tot['recognised']}")
    print(f"sweep recognised, post-extension : {post_tot['recognised']} "
          f"(fitted vocabulary)")
    if pre_tot["recognised"] == 0 and post_tot["recognised"] == 0:
        print("\nDetector 3 reached a judgement on ZERO third-party files, "
              "before OR after fitting its vocabulary to them. Its failure on "
              "external code is structural, not lexical, and the claim now "
              "rests on this corpus rather than on four repositories.")
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "scan_repos.json"), "w", encoding="utf-8") as fh:
        json.dump({"pre": {"total": pre_tot, "per_repo": pre_repo},
                   "post": {"total": post_tot, "per_repo": post_repo}},
                  fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
