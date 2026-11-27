"""Rerun experiments in a scratch copy and compare each result file with the committed one. Committed files are never overwritten.

    python v2/scripts/reproduce.py                                  experiments that need no data
    python v2/scripts/reproduce.py --public-data DIR                adds E13 and E13b (public files, see v2/results/public_data_manifest.txt)
    python v2/scripts/reproduce.py --scorecard DIR                  adds E19b (DIR holds the benchmark's Scorecard.csv)
    python v2/scripts/reproduce.py --cache DIR --labels FILE        adds E3, E8 analysis and E18 (credentialed data, not distributed)
    python v2/scripts/reproduce.py --mutation                       adds E6 (slow)

A number matches if it agrees to a relative tolerance of 1e-9. The comparison was made on the machine that produced the committed
files; other library versions or processors may differ in the last digits of the model-fitting experiments.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def differences(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: present on one side only")
            else:
                differences(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} against {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                differences(x, y, f"{path}[{i}]", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        both_nan = a != a and b != b
        if not (both_nan or a == b or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)):
            out.append(f"{path}: {a} against {b}")
    elif a != b:
        out.append(f"{path}: {a!r} against {b!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--public-data")
    ap.add_argument("--scorecard")
    ap.add_argument("--cache")
    ap.add_argument("--labels")
    ap.add_argument("--mutation", action="store_true")
    a = ap.parse_args()

    # (name, script, arguments, result file)
    jobs = [("E16 analysis", "e16_analysis.py", [], "e16_summary.json"),
            ("E17 degenerate inputs", "e17_degenerate_inputs.py", [], "e17_degenerate_inputs.json"),
            ("E18b rule baselines", "e18b_rule_baselines.py", [], "e18b_rule_baselines.json"),
            ("E22 patched copies", "e22_patched_detectors.py", [], "e22_patched_detectors.json")]
    if a.public_data:
        d = ["--data", os.path.abspath(a.public_data)]
        jobs += [("E13 guarded against unguarded", "e13_guarded_vs_unguarded.py", d, "e13_guarded_vs_unguarded.json"),
                 ("E13b cross-validation", "e13b_cv_bootstrap.py", d, "e13b_cv_bootstrap.json")]
    if a.scorecard:
        jobs.append(("E19b seeded loader comparison", "e19b_seeds.py", ["--data", os.path.abspath(a.scorecard)], "e19b_seeds.json"))
    if a.cache and a.labels:
        cache, labels = os.path.abspath(a.cache), os.path.abspath(a.labels)
        jobs += [("E3 audit size", "e3_d1_audit_size.py", ["--labels", labels], "e3_d1_audit_size.json"),
                 ("E8 family analysis", "e8_family.py", ["analyse", "--cache", cache, "--stored", labels], "e8_family.json"),
                 ("E18 verdict rules", "e18_verdict_rules.py", ["--cache", cache], "e18_verdict_rules.json")]
    if a.mutation:
        jobs.append(("E6 mutation test", "e6_mutation_test.py", ["--workers", "4"], "e6_mutation_test.json"))

    scratch = tempfile.mkdtemp(prefix="reproduce_")
    copy = os.path.join(scratch, "repo")
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "paper", ".pytest_cache"))
    env = dict(os.environ, PCL_TEST_MODE="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    failed = 0
    for name, script, extra, result in jobs:
        produced = os.path.join(copy, "v2", "results", result)
        committed = os.path.join(ROOT, "v2", "results", result)
        if os.path.exists(produced):
            os.remove(produced)  # in the scratch copy only, so that a script that writes nothing cannot pass
        start = time.time()
        run = subprocess.run([sys.executable, "-W", "ignore", os.path.join(copy, "v2", "scripts", script), *extra],
                             cwd=copy, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        took = f"{time.time() - start:.0f}s"
        if run.returncode or not os.path.exists(produced):
            failed += 1
            print(f"FAIL   {name} ({took}): script did not finish\n{run.stderr[-800:]}")
            continue
        out = []
        differences(json.load(open(committed)), json.load(open(produced)), "", out)
        if out:
            failed += 1
            print(f"DIFFER {name} ({took}): {len(out)} values\n   " + "\n   ".join(out[:8]))
        else:
            print(f"MATCH  {name} ({took})", flush=True)
    shutil.rmtree(scratch, ignore_errors=True)
    print(f"{len(jobs) - failed} of {len(jobs)} match")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
