"""E7: blinded rating sheets for the independent second rater (no labels are read or shown).

    python v2/scripts/make_rating_sheets.py --out <directory outside the repository>

Reads the two site samples (task3a_sample.json: 53 selection sites; task4b_sample.json: 88 reachability sites) and the pinned
third-party clones, and writes one markdown sheet per rubric with the code at each site and blank answer fields, plus a
neutral key (site number to repository, file, lines). The order is shuffled with a fixed seed so repositories are mixed.
The label files (task3b_labels.json, task4c_labels.json) are not opened.
"""
import os
import json
import random
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")
CORPUS = os.environ.get("SCAN_CORPUS", r"C:\Users\nikhi\Codes\RES\src\pclCodebase\scan_corpus")
CONTEXT = int(os.environ.get("E7_CONTEXT", "8"))
MAXLINES = int(os.environ.get("E7_MAXLINES", "70"))
SUFFIX = os.environ.get("E7_SUFFIX", "")

SHEETS = {
    "3b": {"sample": "task3a_sample.json", "seed": 20261110, "title": "Rater sheet A: model-selection sites (53)",
           "intro": (
               "For each site decide whether the code chooses a model, checkpoint or hyperparameter using the same held-out, "
               "OOD or test data on which the reported result is measured.\n\n"
               "Labels (pick exactly one): CONTAMINATED = the same held-out/OOD/test split drives the selection and is the split of the "
               "number presented as held-out or zero-shot. DISCLOSED_ORACLE = as CONTAMINATED and the authors say in code or documentation "
               "that this is oracle selection. SOUND = selection uses train or source validation, and the reported number uses a different "
               "split. NOT_SELECTION = the pattern matched but nothing is being chosen. AMBIGUOUS = cannot be established from the file and "
               "the configuration it ships with (read other files if needed and name them).\n\n"
               "Also write the selection split and the reported split, each one of: train, source validation, held-out target, OOD target, "
               "test, unknown.")},
    "4c": {"sample": "task4b_sample.json", "seed": 20261111, "title": "Rater sheet B: reachability sites (88)",
           "intro": (
               "For each site decide whether a degenerate value (NaN, None, an empty collection, a zero standing for 'missing') can reach it "
               "under supported use and silently change the output.\n\n"
               "Labels (pick exactly one): GUARDED = an explicit NaN/None/emptiness check dominates the site in the same function, or the "
               "language raises on the degenerate input, so the failure is loud. UNREACHABLE = the degenerate input is excluded by construction "
               "or by the configuration the repository ships with. REACHABLE_UNGUARDED = a degenerate input is possible under supported use AND "
               "the result then changes silently. NOT_APPLICABLE = no value that can be degenerate is involved, or the site feeds no verdict, "
               "selection or aggregation. If a degenerate input would crash, the label is GUARDED. If it cannot be established, say 'undecidable' "
               "in the note and use NOT_APPLICABLE.\n\n"
               "For REACHABLE_UNGUARDED also say whether the degenerate value arises only when training diverges (answer: diverged-only) or under "
               "ordinary use (answer: ordinary).")},
}


def git_show(repo, sha, path):
    r = subprocess.run(["git", "-C", os.path.join(CORPUS, repo), "show", f"{sha}:{path}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def excerpt(text, start, end):
    lines = text.splitlines()
    lo = max(1, start - CONTEXT)
    hi = min(len(lines), end + CONTEXT)
    if hi - lo + 1 > MAXLINES:
        hi = lo + MAXLINES - 1
    out = []
    for i in range(lo, hi + 1):
        mark = ">" if start <= i <= end else " "
        out.append(f"{mark}{i:5d}  {lines[i - 1]}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for key, cfg in SHEETS.items():
        sites = json.load(open(os.path.join(R1, cfg["sample"])))
        order = list(range(len(sites)))
        random.Random(cfg["seed"]).shuffle(order)
        md = [f"# {cfg['title']}", "", cfg["intro"], "",
              "Do not open any file named *labels*.json in the project. Decide from the code shown and, if needed, from the repository "
              "at the pinned commit. Lines marked with > are the matched lines.", ""]
        key_rows = []
        for n, i in enumerate(order, 1):
            s = sites[i]
            text = git_show(s["repo"], s["sha"], s["file"])
            body = excerpt(text, s["start"], s["end"]) if text else "(file could not be read at the pinned commit)"
            md += [f"## Site {n}: {s['repo']} @ {s['sha']}, `{s['file']}` lines {s['start']}-{s['end']}", "", "```python", body, "```", "",
                   "Label: ______", "Selection split / reported split: ______" if key == "3b" else "Diverged-only or ordinary (if REACHABLE_UNGUARDED): ______",
                   "Note (one line): ______", ""]
            key_rows.append({"site": n, "repo": s["repo"], "sha": s["sha"], "file": s["file"], "start": s["start"], "end": s["end"]})
        open(os.path.join(a.out, f"rater_sheet_{key}{SUFFIX}.md"), "w", encoding="utf-8").write("\n".join(md))
        json.dump(key_rows, open(os.path.join(a.out, f"rater_key_{key}.json"), "w"), indent=1)
        print(key, len(sites), "sites")


if __name__ == "__main__":
    main()
