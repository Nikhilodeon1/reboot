"""List every numeric token in the paper that does not appear in either ledger (round 1 or v2).

    python v2/scripts/numbers_audit.py

A token printed here is not necessarily wrong; it is a token with no ledger row behind it, so a person checks it
(small counts, section numbers and constants fixed in the text are handled by the allowlist below).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
TEX = os.path.join(V2, "paper", "main.tex")
LEDGERS = [os.path.join(V2, "evidence_r1", "rebuttal", "LEDGER.md"), os.path.join(V2, "LEDGER_V2.md")]
NUM = re.compile(r"[-+\u2212$]?\d[\d,]*(?:\.\d+)?")
ALLOW = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "95", "0.05", "0.95", "0.5", "0.60", "0.6", "2026",
         "2024", "2025", "2022", "2023", "2021", "2020", "2019", "2018", "2000", "1960", "1997", "2003", "1.00",
         "100", "1000", "5000", "500", "200", "25", "20"}


def norm(t):
    t = t.replace("\u2212", "-").replace("$", "").replace(",", "").lstrip("+-")
    return t


def tokens(text):
    return {norm(t) for t in NUM.findall(text)}


def main():
    allowed = set()
    for p in LEDGERS:
        allowed |= tokens(open(p, encoding="utf-8").read())
    tex = open(TEX, encoding="utf-8").read()
    tex = re.sub(r"(?m)(?<!\\)%.*$", "", tex)
    tex = tex.split("\\bibliographystyle")[0] + "\n" + tex.split("\\appendix")[1]
    tex = re.sub(r"\\(?:cite[pt]?|ref|label|includegraphics|texttt|pending|input|bibliography)\*?(?:\[[^\]]*\])?\{[^}]*\}", " ", tex)
    unmatched = {}
    for m in NUM.finditer(tex):
        t = norm(m.group(0))
        if t in allowed or t in ALLOW:
            continue
        ctx = tex[max(0, m.start() - 50): m.end() + 30].replace("\n", " ")
        unmatched.setdefault(t, ctx)
    print(f"{len(unmatched)} tokens without a ledger match")
    for t, ctx in sorted(unmatched.items(), key=lambda kv: kv[0]):
        print(f"{t:>10}  ...{ctx}...")


if __name__ == "__main__":
    main()
