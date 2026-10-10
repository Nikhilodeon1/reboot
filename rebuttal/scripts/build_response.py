"""Build the response texts from rebuttal/response_src/*.md.

Every number comes from rebuttal/numbers.json, and every entry names a ledger row. The build
fails if a placeholder is unknown, a ledger id is missing, a number in an entry does not occur
in its ledger row (allowing rounding), a comment is over the character limit, or a banned
phrase or em dash appears. {{SPOTCHECK}} is the one placeholder allowed to stay open.

    python rebuttal/scripts/build_response.py
"""
import os
import re
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REB = os.path.join(ROOT, "rebuttal")
LIMIT = 4800
BANNED = ["delve", "crucially", "it is worth noting", "we thank", "insightful", "misread", "validated",
          "FPR 0", "worse with data", "order of magnitude", "expected direction", "please consider raising",
          "—", " --- "]
OPEN_OK = {"SPOTCHECK"}


def ledger_rows():
    rows = {}
    for ln in open(os.path.join(REB, "LEDGER.md"), encoding="utf-8"):
        if ln.startswith("| ") and not ln.startswith("| id") and not ln.startswith("|---"):
            c = ln.strip().strip("|").split(" | ")
            rows[c[0].strip()] = " ".join(c)
    return rows


NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")


def number_in_row(tok, row):
    clean = tok.lstrip("+-")
    if clean in re.sub(r"[+]", "", row):
        return True
    if "." in clean:
        dec = len(clean.split(".")[1])
        for m in NUM.findall(row):
            if "." in m and abs(round(float(m.lstrip("+")), dec) - float(clean)) < 1e-12:
                return True
    return False


def main():
    rows = ledger_rows()
    nums = json.load(open(os.path.join(REB, "numbers.json"), encoding="utf-8"))
    errors, report = [], []
    for k, v in nums.items():
        if v["ledger"] not in rows:
            errors.append(f"numbers.json[{k}]: ledger id {v['ledger']} not found")
            continue
        for tok in NUM.findall(v["text"]):
            if tok.lstrip("+-") in ("0", "1") and len(tok) == 1:
                continue
            if not number_in_row(tok, rows[v["ledger"]]):
                errors.append(f"numbers.json[{k}]: {tok} not in ledger row {v['ledger']}")
    open_items = []
    src_dir = os.path.join(REB, "response_src")
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith(".md"):
            continue
        name = fn[:-3]
        text = open(os.path.join(src_dir, fn), encoding="utf-8").read()
        used = re.findall(r"\{\{(N:)?([A-Za-z0-9_]+)\}\}", text)

        def sub(m):
            tag, key = m.group(1), m.group(2)
            if not tag:
                if key in OPEN_OK:
                    open_items.append((name, key))
                    return m.group(0)
                errors.append(f"{fn}: unknown open placeholder {{{{{key}}}}}")
                return m.group(0)
            if key not in nums:
                errors.append(f"{fn}: unresolved number {key}")
                return m.group(0)
            return nums[key]["text"]

        out = re.sub(r"\{\{(N:)?([A-Za-z0-9_]+)\}\}", sub, text)
        for b in BANNED:
            if b.lower() in out.lower():
                errors.append(f"{fn}: banned phrase {b!r}")
        n = len(out)
        if n > LIMIT:
            errors.append(f"{fn}: {n} characters, limit {LIMIT}")
        report.append((name, n, len(used)))
        open(os.path.join(REB, f"RESPONSE_{name}.md"), "w", encoding="utf-8", newline="\n").write(out)
    for name, n, k in report:
        print(f"RESPONSE_{name}.md: {n} characters, {k} placeholders")
    for name, key in open_items:
        print(f"OPEN: {{{{{key}}}}} in {name}")
    if errors:
        print("\nBUILD FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("build ok")


if __name__ == "__main__":
    main()
