"""Task 4a: choose up to 10 new repositories by a rule fixed before any query.

For each of five topics, in this order, take the first 2 repositories in GitHub's
star-sorted search results that (a) are Python (query qualifier), (b) have an
associated paper, and (c) are not already in the corpus or already taken for an
earlier topic. No hand-picking: the queries, the paper test and the ordering are
the constants below, committed before the first request is made.

"Has an associated paper" is operationalised mechanically: the repository's
README contains a link to arxiv.org, doi.org, openreview.net, aclanthology.org,
proceedings.mlr.press, proceedings.neurips.cc, dl.acm.org or ieeexplore.ieee.org.

Search results are scanned in rank order, at most the first 30 per topic. Every
skipped result is recorded with its reason. The commit pinned for each chosen
repository is the default-branch HEAD at selection time (`git ls-remote`). If
GitHub is unreachable the script stops and says so.

    python rebuttal/scripts/task4a_select_repos.py
"""
import os
import re
import sys
import json
import time
import subprocess
import urllib.parse
import urllib.request
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOPICS = [
    ("domain generalization benchmark", "domain generalization benchmark"),
    ("distribution shift benchmark", "distribution shift benchmark"),
    ("fairness toolkit", "fairness toolkit"),
    ("hyperparameter / model-selection benchmark", "hyperparameter model selection benchmark"),
    ("calibration / uncertainty evaluation library", "calibration uncertainty evaluation library"),
]
PER_TOPIC = 2
SCAN_DEPTH = 30
PAPER = re.compile(r"(arxiv\.org|doi\.org|openreview\.net|aclanthology\.org|proceedings\.mlr\.press|"
                   r"proceedings\.neurips\.cc|dl\.acm\.org|ieeexplore\.ieee\.org)", re.I)
# the 18 pinned corpus repositories plus AIF360, lower-cased owner/name
ALREADY = {
    "usc-melady/benchmarking_dl_mimiciii", "facebookresearch/domainbed", "mld3/fiddle",
    "ratschlab/hirid-icu-benchmark", "mlforhealth/hurtfulwords", "healthylaife/mimic-iv-data-pipeline",
    "mlforhealth/mimic_extract", "emmarocheteau/tpc-los-prediction", "ratschlab/circews",
    "bvanaken/clinical-outcome-prediction", "emmarocheteau/eicu-gnn-lstm", "mit-lcp/mimic-code",
    "yerevann/mimic3-benchmarks", "clinicalml/omop-learn", "mp2893/retain", "microsoft/robustdg",
    "alistairewj/sepsis3-mimic", "sebbarb/time_aware_attention", "trusted-ai/aif360",
}
UA = {"User-Agent": "reboot-rebuttal-task4a"}


def get(url, accept=None):
    req = urllib.request.Request(url, headers=dict(UA, **({"Accept": accept} if accept else {})))
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", errors="replace")


def readme_text(full):
    for name in ("README.md", "readme.md", "README.rst", "README.MD", "README"):
        try:
            return get(f"https://raw.githubusercontent.com/{full}/HEAD/{name}")
        except Exception:
            continue
    return None


def head_sha(full):
    out = subprocess.run(["git", "ls-remote", f"https://github.com/{full}.git", "HEAD"],
                         capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    return out.stdout.split()[0] if out.stdout.strip() else None


def main():
    taken, record = set(ALREADY), []
    for label, phrase in TOPICS:
        q = f"{phrase} language:python"
        url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) +
               f"&sort=stars&order=desc&per_page={SCAN_DEPTH}")
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            items = json.loads(get(url, "application/vnd.github+json"))["items"]
        except Exception as e:
            sys.exit(f"STOP: GitHub unreachable or rate-limited for topic '{label}': {e}")
        entry = {"topic": label, "query": q, "timestamp_utc": stamp, "scanned": [], "chosen": []}
        for rank, it in enumerate(items, 1):
            full = it["full_name"]
            row = {"rank": rank, "repo": full, "stars": it["stargazers_count"]}
            if full.lower() in taken:
                row["skipped"] = "already included"
            else:
                txt = readme_text(full)
                if txt is None:
                    row["skipped"] = "no README found"
                elif not PAPER.search(txt):
                    row["skipped"] = "README has no paper link"
                else:
                    sha = head_sha(full)
                    if not sha:
                        row["skipped"] = "could not resolve HEAD"
                    else:
                        row["chosen"] = True
                        row["sha"] = sha
                        taken.add(full.lower())
                        entry["chosen"].append(full)
            entry["scanned"].append(row)
            if len(entry["chosen"]) >= PER_TOPIC:
                break
        record.append(entry)
        time.sleep(8)                      # search API allows 10 requests a minute
    os.makedirs(os.path.join(ROOT, "rebuttal", "results"), exist_ok=True)
    json.dump(record, open(os.path.join(ROOT, "rebuttal", "results", "task4a_selection.json"), "w"), indent=1)
    for e in record:
        print(e["topic"], "->", [(r["repo"], r["stars"], r["sha"][:10]) for r in e["scanned"] if r.get("chosen")])


if __name__ == "__main__":
    main()
