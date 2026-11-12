"""Task 3a: enumerate candidate model-selection sites across the pinned corpus.

The patterns below are the committed definition of a candidate site. They are
frozen in a commit of their own before this script is ever run, so the counts
cannot be tuned after seeing them. Third-party code is parsed with `ast`, never
imported or executed.

    python rebuttal/scripts/task3a_enumerate.py --root <corpus dir>

Patterns (a site is the smallest enclosing statement or definition):

  P1 argmax_metric   call to argmax / argmin / max / min that either passes a
                     `key=` argument or has an argument mentioning a metric word
  P2 best_update     `if` whose test compares against a name containing "best"
                     and whose body assigns or calls something save-like
  P3 early_stopping  EarlyStopping-like construction, a `patience` argument or
                     keyword, or a `monitor=` keyword
  P4 named_selector  function definition whose name matches
                     select|best|sweep|tune|hparam

Sampling: per repo, sites are shuffled with a fixed seed; the sample is taken
round-robin across repos (in a seeded repo order), at most 5 per repo, until 60
sites are collected. Files under test directories are excluded and counted.
"""
import os
import re
import ast
import json
import random
import argparse
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 20261006
PER_REPO = 5
CAP = 60

METRIC = re.compile(r"(auc|auroc|auprc|roc|acc|f1|loss|score|metric|kappa|mse|mae|rmse|"
                    r"val|valid|dev|test|best)", re.I)
SELECTOR_NAME = re.compile(r"select|best|sweep|tune|hparam", re.I)
SAVE_LIKE = re.compile(r"save|checkpoint|state_dict|copy|dump", re.I)
EARLY = re.compile(r"early_?stop", re.I)
SKIP_DIR = re.compile(r"(^|/)(tests?|\.git|node_modules)(/|$)")
FUNCS = {"argmax", "argmin", "max", "min"}


def call_name(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def unparse(node):
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def sites_in(tree):
    out = []
    for node in ast.walk(tree):
        end = getattr(node, "end_lineno", getattr(node, "lineno", 0))
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name in FUNCS:
                has_key = any(k.arg == "key" for k in node.keywords)
                text = " ".join(unparse(a) for a in node.args)
                if has_key or METRIC.search(text):
                    out.append(("P1", node.lineno, end))
            if EARLY.search(name) or any(k.arg in ("patience", "monitor")
                                         for k in node.keywords):
                out.append(("P3", node.lineno, end))
        elif isinstance(node, ast.If):
            if "best" in unparse(node.test).lower() and isinstance(node.test, ast.Compare):
                body = " ".join(unparse(s) for s in node.body)
                if any(isinstance(s, (ast.Assign, ast.AugAssign)) for s in node.body) \
                        or SAVE_LIKE.search(body):
                    out.append(("P2", node.lineno, end))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if SELECTOR_NAME.search(node.name):
                out.append(("P4", node.lineno, end))
            if any(a.arg == "patience" for a in node.args.args + node.args.kwonlyargs):
                out.append(("P3", node.lineno, end))
    return out


def read_pins(path):
    pins = {}
    for ln in open(path, encoding="utf-8"):
        parts = ln.split()
        if len(parts) == 3 and re.fullmatch(r"[0-9a-f]{10}", parts[1]):
            pins[parts[0]] = parts[1]
    return pins


def scan_repo(rp):
    rows, stats = [], {"py_files": 0, "parsed": 0, "unparseable": 0, "excluded_test": 0,
                       "ipynb_not_scanned": 0}
    for dp, dn, fn in os.walk(rp):
        dn[:] = [d for d in dn if d != ".git"]
        rel_dir = os.path.relpath(dp, rp).replace("\\", "/")
        for f in sorted(fn):
            rel = f if rel_dir == "." else f"{rel_dir}/{f}"
            if f.endswith(".ipynb"):
                stats["ipynb_not_scanned"] += 1
                continue
            if not f.endswith(".py"):
                continue
            if SKIP_DIR.search(rel):
                stats["excluded_test"] += 1
                continue
            stats["py_files"] += 1
            try:
                tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8",
                                      errors="replace").read())
            except (SyntaxError, ValueError, RecursionError):
                stats["unparseable"] += 1
                continue
            stats["parsed"] += 1
            for pat, a, b in sites_in(tree):
                rows.append({"file": rel, "start": a, "end": b, "pattern": pat})
    # one site per (file, start, pattern)
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: (r["file"], r["start"], r["pattern"])):
        k = (r["file"], r["start"], r["pattern"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(ROOT), "scan_corpus"))
    ap.add_argument("--pins", default=os.path.join(ROOT, "detectors", "external", "SCAN_CORPUS.md"))
    ap.add_argument("--out", default=os.path.join(ROOT, "rebuttal"))
    a = ap.parse_args()

    pins = read_pins(a.pins)
    per_repo, counts = {}, {}
    for repo in sorted(pins):
        rows, stats = scan_repo(os.path.join(a.root, repo))
        per_repo[repo] = rows
        by = defaultdict(int)
        for r in rows:
            by[r["pattern"]] += 1
        counts[repo] = dict(stats, sha=pins[repo], sites=len(rows),
                            **{p: by.get(p, 0) for p in ("P1", "P2", "P3", "P4")})

    rng = random.Random(SEED)
    order = sorted(pins)
    rng.shuffle(order)
    shuffled = {r: random.Random(f"{SEED}-{r}").sample(per_repo[r], len(per_repo[r]))
                for r in order}
    sample = []
    for rank in range(PER_REPO):
        for r in order:
            if len(sample) >= CAP:
                break
            if rank < len(shuffled[r]):
                s = dict(shuffled[r][rank], repo=r, sha=pins[r])
                sample.append(s)

    os.makedirs(os.path.join(a.out, "results"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "tables"), exist_ok=True)
    json.dump({"seed": SEED, "per_repo_cap": PER_REPO, "cap": CAP, "repo_order": order,
               "counts": counts, "total_sites": sum(c["sites"] for c in counts.values()),
               "sampled": len(sample)},
              open(os.path.join(a.out, "results", "task3a_counts.json"), "w"), indent=1)
    json.dump(sample, open(os.path.join(a.out, "results", "task3a_sample.json"), "w"), indent=1)
    with open(os.path.join(a.out, "tables", "task3a_counts_by_repo.csv"), "w") as fh:
        fh.write("repo,sha,py_files,parsed,unparseable,excluded_test,ipynb_not_scanned,"
                 "sites,P1,P2,P3,P4,sampled\n")
        ns = defaultdict(int)
        for s in sample:
            ns[s["repo"]] += 1
        for r in sorted(counts):
            c = counts[r]
            fh.write(f"{r},{c['sha']},{c['py_files']},{c['parsed']},{c['unparseable']},"
                     f"{c['excluded_test']},{c['ipynb_not_scanned']},{c['sites']},"
                     f"{c['P1']},{c['P2']},{c['P3']},{c['P4']},{ns[r]}\n")
    print(f"repos {len(counts)}  sites {sum(c['sites'] for c in counts.values())}  "
          f"sampled {len(sample)}")


if __name__ == "__main__":
    main()
