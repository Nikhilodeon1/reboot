"""Check a rater's JSON file before it is analysed.

    python v2/scripts/e7_validate.py <rater json> <3b|4c>

Reports whether the file parses, has one entry per site (53 or 88), uses only allowed labels, and lists any missing or duplicate site numbers.
"""
import sys
import json
import collections

ALLOWED = {"3b": ({"CONTAMINATED", "DISCLOSED_ORACLE", "SOUND", "NOT_SELECTION", "AMBIGUOUS"}, 53),
           "4c": ({"GUARDED", "UNREACHABLE", "REACHABLE_UNGUARDED", "NOT_APPLICABLE"}, 88)}


def main():
    path, sheet = sys.argv[1], sys.argv[2]
    labels, n = ALLOWED[sheet]
    text = open(path, encoding="utf-8").read().strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
        print("note: markdown fences removed for this check; remove them from the file")
    data = json.loads(text)
    sites = [d.get("site") for d in data]
    dup = [s for s, c in collections.Counter(sites).items() if c > 1]
    miss = [s for s in range(1, n + 1) if s not in sites]
    bad = [(d.get("site"), d.get("label")) for d in data if d.get("label") not in labels]
    print(f"entries {len(data)} of {n}; duplicates {dup}; missing {miss}; bad labels {bad}")
    print(dict(collections.Counter(d.get("label") for d in data)))
    print("OK" if len(data) == n and not dup and not miss and not bad else "PROBLEM")


if __name__ == "__main__":
    main()
