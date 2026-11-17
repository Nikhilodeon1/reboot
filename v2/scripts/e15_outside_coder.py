"""E15 (PREREG_V2_ADDENDUM_6.md): sheet for an outside human coder, and scoring of the returned labels.

    python v2/scripts/e15_outside_coder.py draw  --out <dir for the coder> --private <dir for the key, outside the repository>
    python v2/scripts/e15_outside_coder.py score --private <dir> --responses <responses.csv> [--results v2/results/e15_outside_coder.json]

draw: picks the 40 sites (all 16 labelled REACHABLE_UNGUARDED, 12 of 32 GUARDED/UNREACHABLE, 12 of 40 NOT_APPLICABLE; numpy seed 20261116),
shuffles them, and writes the coder's sheet (code and marked lines, no labels), a blank responses.csv and a table of repository URLs. The key
and the sampling record go to --private. Our labels are read only to stratify and are never written to the coder's folder.
score: compares the returned labels with ours (weights, kappa, agreement, counts); see the addendum for what is reported.
"""
import os
import sys
import csv
import json
import random
import argparse
import subprocess
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")
CORPUS = os.environ.get("SCAN_CORPUS", "")
CONTEXT, MAXLINES = 8, 70
LABELS = ["GUARDED", "UNREACHABLE", "REACHABLE_UNGUARDED", "NOT_APPLICABLE"]
SEED = 20261116
INTRO = """# Coding sheet: where can a degenerate value silently change a result?

You are labelling 40 places in public Python code (each shown with the matched lines marked by >). Please do not use any language model or
ask anyone else, and do not look up other people's labels. Work from the code shown, and from the repository at the pinned commit if you need more
context (repositories.md has the links). About 3 to 5 minutes per site is typical. Fill in responses.csv (one row per site) or write the
labels directly under each site below. Anything you cannot establish from the code is allowed to be 'undecidable' (see the rule at the end).

**The question for each site.** Can a degenerate value (NaN, None, an empty collection, or a zero that stands for 'missing') reach this
place under normal, supported use of the repository, and if it does, does the result change silently instead of failing loudly?

**Labels (pick exactly one).**

| Label | Rule |
|---|---|
| GUARDED | An explicit NaN / None / emptiness check dominates the site in the same function, or the language raises on the degenerate input (for example `max([])` raises ValueError), so the failure is loud rather than silent. |
| UNREACHABLE | The degenerate input is excluded by construction or by the configuration the repository ships with (a collection built non-empty, a constant, an asserted precondition, a fixed config). |
| REACHABLE_UNGUARDED | A degenerate input is possible under supported use AND, if it occurs, the result changes silently (for example `any([])` is False so a check passes, `all([])` is True, a NaN first element wins or loses a comparison, a missing key set is taken from the first element). |
| NOT_APPLICABLE | The matched pattern involves no value that can be degenerate in this sense (loop counters, shapes, string handling, literal constants), or the site does not feed a verdict, selection or aggregation. |

**Rules.**
1. If a degenerate input would crash, the label is GUARDED, not REACHABLE_UNGUARDED.
2. If it cannot be established, use the more cautious label: UNREACHABLE only when the exclusion is demonstrated, REACHABLE_UNGUARDED only when
   the silent change is demonstrated. A site you cannot decide is recorded as NOT_APPLICABLE with the note `undecidable`.
3. For REACHABLE_UNGUARDED, also say whether the degenerate value arises only when training diverges (`diverged-only`) or under ordinary use
   (`ordinary`).
4. Write one line of reasoning per site; it helps us understand disagreements and is not scored.
"""


def git_show(repo, sha, path):
    r = subprocess.run(["git", "-C", os.path.join(CORPUS, repo), "show", f"{sha}:{path}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def excerpt(text, start, end):
    lines = text.splitlines()
    lo, hi = max(1, start - CONTEXT), min(len(lines), end + CONTEXT)
    if hi - lo + 1 > MAXLINES:
        hi = lo + MAXLINES - 1
    return "\n".join(f"{'>' if start <= i <= end else ' '}{i:5d}  {lines[i - 1]}" for i in range(lo, hi + 1))


def sample():
    sites = json.load(open(os.path.join(R1, "task4b_sample.json")))
    lab = {x["idx"]: x for x in json.load(open(os.path.join(R1, "task4c_labels.json")))}
    strata = {"positive": [], "other_applicable": [], "not_applicable": []}
    for i in range(len(sites)):
        l = lab[i]["label"]
        if l == "REACHABLE_UNGUARDED" or lab[i].get("divergence_only"):      # the 16 sites counted under the broad reading
            strata["positive"].append(i)
        elif l in ("GUARDED", "UNREACHABLE"):
            strata["other_applicable"].append(i)
        else:
            strata["not_applicable"].append(i)
    rng = np.random.default_rng(SEED)
    chosen = {"positive": sorted(strata["positive"]),
              "other_applicable": sorted(rng.choice(strata["other_applicable"], 12, replace=False).tolist()),
              "not_applicable": sorted(rng.choice(strata["not_applicable"], 12, replace=False).tolist())}
    return sites, lab, strata, chosen


def draw(a):
    sites, lab, strata, chosen = sample()
    assert [len(strata[k]) for k in ("positive", "other_applicable", "not_applicable")] == [16, 32, 40], {k: len(v) for k, v in strata.items()}
    order = [i for k in chosen for i in chosen[k]]
    random.Random(SEED).shuffle(order)
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.private, exist_ok=True)
    md = [INTRO, ""]
    key, urls = [], {}
    for n, i in enumerate(order, 1):
        s = sites[i]
        text = git_show(s["repo"], s["sha"], s["file"])
        body = excerpt(text, s["start"], s["end"]) if text else "(file could not be read at the pinned commit)"
        md += [f"## Site {n}: {s['repo']} @ {s['sha']}, `{s['file']}` lines {s['start']}-{s['end']}", "", "```python", body, "```", "",
               "Label: ______", "diverged-only or ordinary (only if REACHABLE_UNGUARDED): ______", "Note (one line): ______", ""]
        stratum = next(k for k in chosen if i in chosen[k])
        key.append({"site": n, "idx": i, "stratum": stratum, "our_label": lab[i]["label"], "our_divergence_only": lab[i].get("divergence_only", False),
                    "repo": s["repo"], "sha": s["sha"], "file": s["file"], "start": s["start"], "end": s["end"]})
        if s["repo"] not in urls:
            r = subprocess.run(["git", "-C", os.path.join(CORPUS, s["repo"]), "remote", "get-url", "origin"], capture_output=True, text=True)
            urls[s["repo"]] = r.stdout.strip()
    open(os.path.join(a.out, "coding_sheet.md"), "w", encoding="utf-8").write("\n".join(md))
    with open(os.path.join(a.out, "responses.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["site", "label", "diverged_only_or_ordinary", "note"])
        for k in key:
            w.writerow([k["site"], "", "", ""])
    open(os.path.join(a.out, "repositories.md"), "w", encoding="utf-8").write(
        "# Repositories (public)\n\nOpen the pinned commit shown in the sheet: replace COMMIT in `<url>/tree/COMMIT`.\n\n"
        + "\n".join(f"- {r}: {u}" for r, u in sorted(urls.items())) + "\n")
    json.dump({"seed": SEED, "strata_sizes": {k: len(v) for k, v in strata.items()}, "sampled": {k: len(v) for k, v in chosen.items()}, "key": key},
              open(os.path.join(a.private, "e15_key.json"), "w"), indent=1)
    print("sites", len(key), "strata", {k: len(v) for k, v in chosen.items()})


def kappa_w(y1, y2, w):
    labs = sorted(set(y1) | set(y2))
    w = np.asarray(w, float)
    po = float(np.sum(w * np.array([a == b for a, b in zip(y1, y2)])) / w.sum())
    pe = sum((float(np.sum(w * (np.array(y1) == l))) / w.sum()) * (float(np.sum(w * (np.array(y2) == l))) / w.sum()) for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - a / 2, k + 1, n - k)
    return [float(lo), float(hi)]


def score(a):
    key = json.load(open(os.path.join(a.private, "e15_key.json")))["key"]
    resp = {int(r["site"]): r for r in csv.DictReader(open(a.responses, encoding="utf-8"))}
    sizes = {"positive": (16, 16), "other_applicable": (32, 12), "not_applicable": (40, 12)}
    ours, theirs, w, st = [], [], [], []
    for k in key:
        r = resp[k["site"]]
        lab = r["label"].strip().upper()
        assert lab in LABELS, (k["site"], lab)
        ours.append("RU_diverged" if k["our_divergence_only"] else "RU_ordinary" if k["our_label"] == "REACHABLE_UNGUARDED" else k["our_label"])
        div = str(r["diverged_only_or_ordinary"]).strip().lower()
        theirs.append(("RU_diverged" if div.startswith("diverged") else "RU_ordinary") if lab == "REACHABLE_UNGUARDED" else lab); st.append(k["stratum"]); w.append(sizes[k["stratum"]][0] / sizes[k["stratum"]][1])
    out = {"n": len(key), "per_stratum_agreement": {}, "disagreements": []}
    for s_ in sizes:
        idx = [i for i, x in enumerate(st) if x == s_]
        ag = sum(ours[i] == theirs[i] for i in idx)
        out["per_stratum_agreement"][s_] = {"agree": ag, "n": len(idx), "cp95": cp(ag, len(idx))}
    col = lambda x: "REACHABLE_UNGUARDED" if x.startswith("RU_") else x
    out["weighted_kappa_five_classes"] = kappa_w(ours, theirs, w)
    out["weighted_kappa_four_labels"] = kappa_w([col(x) for x in ours], [col(x) for x in theirs], w)
    ours_raw = ours
    ours = [col(x) for x in ours]
    theirs_raw = theirs
    theirs = [col(x) for x in theirs]
    rng = np.random.default_rng(0)
    bs = []
    for _ in range(2000):
        j = rng.integers(0, len(key), len(key))
        try:
            bs.append(kappa_w([ours[i] for i in j], [theirs[i] for i in j], [w[i] for i in j]))
        except Exception:
            pass
    out["weighted_kappa_bootstrap_95"] = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]
    b1 = [o == "REACHABLE_UNGUARDED" for o in ours]
    b2 = [t == "REACHABLE_UNGUARDED" for t in theirs]
    out["weighted_kappa_binary_reachable_unguarded"] = kappa_w(b1, b2, w)
    pos_idx = [i for i, x in enumerate(st) if x == "positive"]
    out["of_our_16_positives_coder_labels_reachable_unguarded"] = sum(theirs[i] == "REACHABLE_UNGUARDED" for i in pos_idx)
    # counts scaled to the 88 by stratum weights; applicable = not NOT_APPLICABLE
    ru = sum(w[i] for i in range(len(key)) if theirs[i] == "REACHABLE_UNGUARDED")
    app = sum(w[i] for i in range(len(key)) if theirs[i] != "NOT_APPLICABLE")
    ru_ord = sum(w[i] for i in range(len(key)) if theirs_raw[i] == "RU_ordinary")
    out["scaled_to_88"] = {"reachable_unguarded_broad": ru, "reachable_unguarded_narrow_ordinary_only": ru_ord, "applicable": app}
    for i, k in enumerate(key):
        if ours[i] != theirs[i]:
            out["disagreements"].append({"site": k["site"], "repo": k["repo"], "file": k["file"], "start": k["start"], "ours": ours_raw[i], "coder": theirs_raw[i],
                                         "coder_note": resp[k["site"]]["note"]})
    json.dump(out, open(a.results, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "disagreements"}, indent=1), "disagreements", len(out["disagreements"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["draw", "score"])
    ap.add_argument("--out")
    ap.add_argument("--private", required=True)
    ap.add_argument("--responses")
    ap.add_argument("--results", default=os.path.join(V2, "results", "e15_outside_coder.json"))
    a = ap.parse_args()
    if not CORPUS:
        sys.exit("set SCAN_CORPUS to the folder with the pinned clones")
    draw(a) if a.mode == "draw" else score(a)
