"""Print the first sentence and word count of every paragraph in the main text, for the 'first sentence states the claim' check."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(os.path.dirname(HERE), "paper", "main.tex"), encoding="utf-8").read()
body = t.split(r"\begin{document}")[1].split(r"\appendix")[0]
body = re.sub(r"(?m)%.*$", "", body)
for env in ("table", "figure", "tikzpicture", "tabular"):
    body = re.sub(r"\\begin\{" + env + r"\*?\}.*?\\end\{" + env + r"\*?\}", "", body, flags=re.S)
paras = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.split()) > 12]
for i, p in enumerate(paras, 1):
    clean = re.sub(r"\\(?:cite[pt]?|ref|label|pending)\*?(?:\[[^\]]*\])?\{[^}]*\}", "", p)
    clean = re.sub(r"\\paragraph\{([^}]*)\}", r"[\1] ", clean)
    clean = re.sub(r"\\[a-zA-Z]+\*?", "", clean)
    clean = re.sub(r"[{}$~]", "", clean).strip()
    first = re.split(r"(?<=[.!?])\s+(?=[A-Z\[])", clean)[0]
    print(f"{i:2d} ({len(clean.split()):3d}w) {first[:230]}")
