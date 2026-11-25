"""Agreement between two answer files for the reporting card (v2/validation_kit/CARD.md).

    python v2/validation_kit/score_agreement.py answers_authors.csv answers_rater.csv

Items answered `unclear` or left empty by either person are listed and excluded from the agreement counts. Cohen's kappa is computed
over the remaining items on the codes as given.
"""
import csv
import sys
from collections import Counter


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["case"], r["item"]): r["answer"].strip().lower() for r in csv.DictReader(f)}


def kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return 1.0 if pe >= 1 else (po - pe) / (1 - pe)


def main():
    A, B = load(sys.argv[1]), load(sys.argv[2])
    keys = sorted(set(A) & set(B))
    used = [k for k in keys if A[k] not in ("", "unclear") and B[k] not in ("", "unclear")]
    skipped = [k for k in keys if k not in used]
    a, b = [A[k] for k in used], [B[k] for k in used]
    agree = sum(x == y for x, y in zip(a, b))
    print(f"items answered by both: {len(used)} of {len(keys)}; skipped as unclear or empty: {len(skipped)}")
    print(f"agreement: {agree} of {len(used)}" + (f" ({100 * agree / len(used):.0f}%)" if used else ""))
    print(f"Cohen's kappa over the codes: {kappa(a, b):.2f}")
    per = {}
    for k in used:
        per.setdefault(k[1], []).append(A[k] == B[k])
    for item, v in sorted(per.items()):
        print(f"  {item}: {sum(v)} of {len(v)}")
    for k in used:
        if A[k] != B[k]:
            print(f"disagreement {k}: authors={A[k]} rater={B[k]}")
    for k in skipped:
        print(f"skipped {k}: authors={A.get(k)} rater={B.get(k)}")


if __name__ == "__main__":
    main()
