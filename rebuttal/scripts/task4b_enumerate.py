"""Task 4b: enumerate Type 1 candidate sites (S1-S4) across the extended corpus.

Patterns are frozen in a commit of their own before this is run. Third-party code
is parsed with `ast`, never imported or executed.

    python -W ignore rebuttal/scripts/task4b_enumerate.py --root <corpus dir>

  S1 selection_extreme   max / min / argmax / argmin with `key=` or a metric-word
                         argument; or `sorted(...)[0]` / `sorted(...)[-1]`
  S2 metric_threshold    ordering comparison (> >= < <=) where one side mentions
                         a metric word and the other is a numeric constant or a
                         threshold-like name
  S3 any_all_guard       `any(...)` / `all(...)` over a comprehension that
                         contains a comparison, or over a bare name / attribute /
                         subscript (a possibly-empty collection)
  S4 first_element_keys  iteration, `.keys()/.items()/.values()`, `set/list/sorted`
                         or `next(iter(...))` taken over element 0 or -1 of a
                         collection, so the key set comes from the first element

Corpus: the 18 pinned repositories (SCAN_CORPUS.md), AIF360 and the repositories
chosen by task4a_select_repos.py, at the SHAs they were cloned at.

Sampling: at most 2 sites per (repo, pattern), seeded; round-robin in seeded
(repo, pattern) order, rank 0 of every group before any rank 1, until 120 sites.
"""
import os
import re
import ast
import json
import random
import argparse
import subprocess
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 20261008
PER_GROUP = 2
CAP = 120

METRIC = re.compile(r"(acc|auc|auroc|auprc|f1|loss|score|metric|kappa|mse|mae|rmse|err|ece|"
                    r"brier|nll|perf|worst)", re.I)
THRESH = re.compile(r"(thresh|tol|cutoff|margin|delta|alpha|eps|target|best|baseline)", re.I)
SKIP_DIR = re.compile(r"(^|/)(tests?|\.git|node_modules)(/|$)")
PICK = {"argmax", "argmin", "max", "min"}
ITER_FNS = {"set", "list", "sorted", "tuple", "dict", "sum", "len"}


def unparse(n):
    try:
        return ast.unparse(n)
    except Exception:
        return ""


def fname(n):
    f = n.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")


def first_or_last(n):
    return (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
            and n.slice.value in (0, -1))


def has_compare(n):
    return any(isinstance(x, ast.Compare) for x in ast.walk(n))


def sites_in(tree):
    out = []
    for n in ast.walk(tree):
        a, b = getattr(n, "lineno", 0), getattr(n, "end_lineno", getattr(n, "lineno", 0))
        if isinstance(n, ast.Call):
            nm = fname(n)
            if nm in PICK and (any(k.arg == "key" for k in n.keywords)
                               or METRIC.search(" ".join(unparse(x) for x in n.args))):
                out.append(("S1", a, b))
            if nm in ("any", "all") and n.args:
                x = n.args[0]
                if isinstance(x, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
                    if has_compare(x):
                        out.append(("S3", a, b))
                elif isinstance(x, (ast.Name, ast.Attribute, ast.Subscript)):
                    out.append(("S3", a, b))
            if nm == "next" and n.args and isinstance(n.args[0], ast.Call) and fname(n.args[0]) == "iter":
                out.append(("S4", a, b))
            if nm in ITER_FNS and n.args and (first_or_last(n.args[0]) or (
                    isinstance(n.args[0], ast.Call) and fname(n.args[0]) in ("keys", "items", "values")
                    and isinstance(n.args[0].func, ast.Attribute) and first_or_last(n.args[0].func.value))):
                if nm != "len" and nm != "sum":
                    out.append(("S4", a, b))
            if nm in ("keys", "items", "values") and isinstance(n.func, ast.Attribute) \
                    and first_or_last(n.func.value):
                out.append(("S4", a, b))
        elif isinstance(n, ast.Subscript):
            if first_or_last(n) and isinstance(n.value, ast.Call) and fname(n.value) == "sorted":
                out.append(("S1", a, b))
        elif isinstance(n, ast.Compare):
            if all(isinstance(o, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)) for o in n.ops):
                left = unparse(n.left)
                right = " ".join(unparse(c) for c in n.comparators)
                const = lambda s: re.fullmatch(r"-?\d+(\.\d+)?(e-?\d+)?", s.strip()) is not None
                if (METRIC.search(left) and (const(right) or THRESH.search(right))) or \
                        (METRIC.search(right) and (const(left) or THRESH.search(left))):
                    out.append(("S2", a, b))
        if isinstance(n, (ast.For, ast.AsyncFor)):
            it = n.iter
            if first_or_last(it) or (isinstance(it, ast.Call) and fname(it) in ("keys", "items", "values")
                                     and isinstance(it.func, ast.Attribute) and first_or_last(it.func.value)):
                out.append(("S4", a, b))
        if isinstance(n, ast.comprehension):
            it = n.iter
            if first_or_last(it) or (isinstance(it, ast.Call) and fname(it) in ("keys", "items", "values")
                                     and isinstance(it.func, ast.Attribute) and first_or_last(it.func.value)):
                out.append(("S4", getattr(it, "lineno", 0), getattr(it, "end_lineno", 0)))
    return out


def scan_repo(rp):
    rows, st = [], {"py_files": 0, "parsed": 0, "unparseable": 0, "excluded_test": 0, "ipynb_not_scanned": 0}
    for dp, dn, fn in os.walk(rp):
        dn[:] = [d for d in dn if d != ".git"]
        rd = os.path.relpath(dp, rp).replace("\\", "/")
        for f in sorted(fn):
            rel = f if rd == "." else f"{rd}/{f}"
            if f.endswith(".ipynb"):
                st["ipynb_not_scanned"] += 1
                continue
            if not f.endswith(".py"):
                continue
            if SKIP_DIR.search(rel):
                st["excluded_test"] += 1
                continue
            st["py_files"] += 1
            try:
                tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8", errors="replace").read())
            except (SyntaxError, ValueError, RecursionError):
                st["unparseable"] += 1
                continue
            st["parsed"] += 1
            for pat, s, e in sites_in(tree):
                rows.append({"file": rel, "start": s, "end": e, "pattern": pat})
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: (r["file"], r["start"], r["pattern"])):
        k = (r["file"], r["start"], r["pattern"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq, st


def pins(corpus):
    p = {}
    for ln in open(os.path.join(ROOT, "detectors", "external", "SCAN_CORPUS.md"), encoding="utf-8"):
        t = ln.split()
        if len(t) == 3 and re.fullmatch(r"[0-9a-f]{10}", t[1]):
            p[t[0]] = t[1]
    newf = os.path.join(corpus, "pins_new.txt")
    for ln in open(newf, encoding="utf-8"):
        t = ln.split()
        if t:
            p[t[0]] = None
    for r in p:
        sha = subprocess.run(["git", "-C", os.path.join(corpus, r), "rev-parse", "HEAD"],
                             capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
        p[r] = sha[:10] if sha else None
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(ROOT), "scan_corpus"))
    ap.add_argument("--out", default=os.path.join(ROOT, "rebuttal"))
    a = ap.parse_args()
    P = pins(a.root)
    per, counts = {}, {}
    for repo in sorted(P):
        rows, st = scan_repo(os.path.join(a.root, repo))
        per[repo] = rows
        by = defaultdict(int)
        for r in rows:
            by[r["pattern"]] += 1
        counts[repo] = dict(st, sha=P[repo], sites=len(rows), **{k: by.get(k, 0) for k in ("S1", "S2", "S3", "S4")})
    groups = [(r, p) for r in sorted(P) for p in ("S1", "S2", "S3", "S4")]
    random.Random(SEED).shuffle(groups)
    pools = {g: random.Random(f"{SEED}-{g[0]}-{g[1]}").sample(
        [x for x in per[g[0]] if x["pattern"] == g[1]], sum(1 for x in per[g[0]] if x["pattern"] == g[1]))
        for g in groups}
    sample = []
    for rank in range(PER_GROUP):
        for g in groups:
            if len(sample) >= CAP:
                break
            if rank < len(pools[g]):
                sample.append(dict(pools[g][rank], repo=g[0], sha=P[g[0]]))
    os.makedirs(os.path.join(a.out, "results"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "tables"), exist_ok=True)
    json.dump({"seed": SEED, "per_group": PER_GROUP, "cap": CAP, "counts": counts,
               "total_sites": sum(c["sites"] for c in counts.values()), "sampled": len(sample)},
              open(os.path.join(a.out, "results", "task4b_counts.json"), "w"), indent=1)
    json.dump(sample, open(os.path.join(a.out, "results", "task4b_sample.json"), "w"), indent=1)
    with open(os.path.join(a.out, "tables", "task4b_counts_by_repo.csv"), "w") as fh:
        fh.write("repo,sha,py_files,parsed,unparseable,excluded_test,ipynb_not_scanned,sites,S1,S2,S3,S4,sampled\n")
        ns = defaultdict(int)
        for s in sample:
            ns[s["repo"]] += 1
        for r in sorted(counts):
            c = counts[r]
            fh.write(f"{r},{c['sha']},{c['py_files']},{c['parsed']},{c['unparseable']},{c['excluded_test']},"
                     f"{c['ipynb_not_scanned']},{c['sites']},{c['S1']},{c['S2']},{c['S3']},{c['S4']},{ns[r]}\n")
    print(f"repos {len(counts)} sites {sum(c['sites'] for c in counts.values())} sampled {len(sample)}")


if __name__ == "__main__":
    main()
