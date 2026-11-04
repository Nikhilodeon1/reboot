"""Check that every key cited in the paper is in ref.bib, every entry in ref.bib is cited, and every entry has a row in CITATIONS_V2.md.

    python v2/scripts/cite_check.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
tex = open(os.path.join(V2, "paper", "main.tex"), encoding="utf-8").read()
bib = open(os.path.join(V2, "paper", "ref.bib"), encoding="utf-8").read()
led = open(os.path.join(V2, "CITATIONS_V2.md"), encoding="utf-8").read()
cited = {k.strip() for m in re.findall(r"\\cite[pt]?\{([^}]*)\}", tex) for k in m.split(",")}
entries = set(re.findall(r"^@\w+\{([^,]+),", bib, flags=re.M))
rows = set(re.findall(r"^\| ([A-Za-z0-9_]+) \|", led, flags=re.M))
print("cited", len(cited), "| entries", len(entries), "| ledger rows", len(rows))
print("cited but not in bib:", sorted(cited - entries))
print("in bib but not cited:", sorted(entries - cited))
print("in bib but no ledger row:", sorted(entries - rows))
print("ledger rows with no bib entry:", sorted(r for r in rows - entries if r not in ("Key",)))
