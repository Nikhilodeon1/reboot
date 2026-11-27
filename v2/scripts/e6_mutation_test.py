"""E6 (PREREG_V2_ADDENDUM_3.md): mutation test of the decision code of detectors 1 and 2, in a scratch copy of the repository.

    PCL_TEST_MODE=1 PHYSIONET_DIR=... python -W ignore v2/scripts/e6_mutation_test.py --workers 3 [--limit N]

Nothing under the repository is edited: the code is copied to a scratch directory per worker, one mutant is written into the copy, the test suite
is run, and the file is restored. Writes aggregates and the survivor list.
"""
import os
import ast
import sys
import json
import shutil
import argparse
import subprocess
import tempfile
import collections
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from stats_util import clopper_pearson

TARGETS = ["detectors/checks/check1_label_shift.py", "detectors/checks/check2_pretrain_leakage.py"]
CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt}
CMP2 = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE}
ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}


def docstring_ids(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant):
                ids.add(id(b.value))
    return ids


def sites(tree):
    """List of (kind, index of node in ast.walk order, lineno, description)."""
    skip = docstring_ids(tree)
    out = []
    for idx, n in enumerate(ast.walk(tree)):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in CMP:
            out.append(("cmp_eq_flip", idx, n.lineno, f"{type(n.ops[0]).__name__} -> {CMP[type(n.ops[0])].__name__}"))
            out.append(("cmp_swap", idx, n.lineno, f"{type(n.ops[0]).__name__} -> {CMP2[type(n.ops[0])].__name__}"))
        elif isinstance(n, ast.BoolOp):
            out.append(("boolop", idx, n.lineno, f"{type(n.op).__name__} -> {'Or' if isinstance(n.op, ast.And) else 'And'}"))
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            out.append(("not_removed", idx, n.lineno, "not removed"))
        elif isinstance(n, ast.BinOp) and type(n.op) in ARITH:
            out.append(("arith", idx, n.lineno, f"{type(n.op).__name__} -> {ARITH[type(n.op)].__name__}"))
        elif isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) and id(n) not in skip:
            out.append(("const_plus1", idx, n.lineno, f"{n.value!r} -> {n.value + 1!r}"))
            out.append(("const_zero", idx, n.lineno, f"{n.value!r} -> 0"))
    return out


def mutate(src, kind, idx):
    tree = ast.parse(src)
    nodes = list(ast.walk(tree))
    n = nodes[idx]
    if kind == "cmp_eq_flip":
        n.ops[0] = CMP[type(n.ops[0])]()
    elif kind == "cmp_swap":
        n.ops[0] = CMP2[type(n.ops[0])]()
    elif kind == "boolop":
        n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
    elif kind == "not_removed":
        parent = next(p for p in nodes for c in ast.iter_child_nodes(p) if c is n)
        for field, val in ast.iter_fields(parent):
            if val is n:
                setattr(parent, field, n.operand)
            elif isinstance(val, list):
                for i, v in enumerate(val):
                    if v is n:
                        val[i] = n.operand
    elif kind == "arith":
        n.op = ARITH[type(n.op)]()
    elif kind == "const_plus1":
        n.value = n.value + 1
    elif kind == "const_zero":
        n.value = type(n.value)(0)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def copy_repo(dst):
    ignore = shutil.ignore_patterns("__pycache__", "*.npz", "*.pt", "*.pkl", ".git", "v2", "fromPod", "rebuttal", "*.pdf", "logs")
    for d in ("detectors", "src", "scripts"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d), ignore=ignore)
    shutil.copy(os.path.join(ROOT, "config.py"), os.path.join(dst, "config.py"))


def run_tests(workdir, env):
    try:
        r = subprocess.run([sys.executable, "-W", "ignore", "-m", "pytest", "detectors/tests", "-x", "-q", "-p", "no:cacheprovider"],
                           cwd=workdir, env=env, capture_output=True, text=True, timeout=180)
        return r.returncode
    except subprocess.TimeoutExpired:
        return "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "v2", "results"))
    a = ap.parse_args()
    originals = {t: open(os.path.join(ROOT, t), encoding="utf-8").read() for t in TARGETS}
    jobs = []
    for t, src in originals.items():
        tree = ast.parse(src)
        for kind, idx, line, desc in sites(tree):
            try:
                m = mutate(src, kind, idx)
                ast.parse(m)
            except Exception:
                continue
            if m == ast.unparse(ast.parse(src)):
                continue
            jobs.append({"file": t, "kind": kind, "line": line, "change": desc, "src": m})
    if a.limit:
        jobs = jobs[: a.limit]
    print(len(jobs), "mutants", flush=True)
    base = tempfile.mkdtemp(prefix="e6_")
    dirs = []
    for w in range(a.workers):
        d = os.path.join(base, f"w{w}")
        os.makedirs(d)
        copy_repo(d)
        dirs.append(d)
    env0 = dict(os.environ)
    # baseline: the unmutated copy must pass, or the experiment is void
    envb = dict(env0, PYTHONPATH=dirs[0])
    if run_tests(dirs[0], envb) != 0:
        sys.exit("baseline test run failed in the scratch copy; mutation test void")
    q = collections.deque(range(len(jobs)))
    results = [None] * len(jobs)

    def worker(w):
        d = dirs[w]
        env = dict(env0, PYTHONPATH=d)
        while True:
            try:
                i = q.popleft()
            except IndexError:
                return
            j = jobs[i]
            path = os.path.join(d, j["file"])
            keep = open(path, encoding="utf-8").read()
            try:
                open(path, "w", encoding="utf-8").write(j["src"])
                rc = run_tests(d, env)
            finally:
                open(path, "w", encoding="utf-8").write(keep)
            results[i] = {k: j[k] for k in ("file", "kind", "line", "change")}
            results[i]["outcome"] = "killed" if rc != 0 else "survived"
            results[i]["detail"] = "timeout" if rc == "timeout" else rc
            if (i + 1) % 20 == 0:
                print("done", sum(r is not None for r in results), "of", len(jobs), flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(worker, range(a.workers)))
    shutil.rmtree(base, ignore_errors=True)
    n = len(results)
    killed = sum(r["outcome"] == "killed" for r in results)
    by_file = {}
    for t in TARGETS:
        rs = [r for r in results if r["file"] == t]
        k = sum(r["outcome"] == "killed" for r in rs)
        by_file[t] = {"mutants": len(rs), "killed": k, "cp95_killed_share": clopper_pearson(k, len(rs))}
    by_kind = collections.Counter((r["kind"], r["outcome"]) for r in results)
    out = {"mutants": n, "killed": killed, "survived": n - killed, "cp95_killed_share": clopper_pearson(killed, n),
           "by_file": by_file, "by_kind": {f"{k[0]}:{k[1]}": v for k, v in sorted(by_kind.items())},
           "survivors": [r for r in results if r["outcome"] == "survived"]}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "e6_mutation_test.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "survivors"}, indent=1))
    print(len(out["survivors"]), "survivors")


if __name__ == "__main__":
    main()
