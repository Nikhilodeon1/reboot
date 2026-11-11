"""Checklist audit of the paper source against the writing skills (voice, rules, citations).

    python v2/scripts/skill_audit.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), "paper", "main.tex")
t = open(TEX, encoding="utf-8").read()
abs_ = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S).group(1)
sents = [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", abs_.strip()) if x]
print("abstract sentences:", len(sents), "| words:", len(abs_.split()), "(skill: 5 to 12 sentences)")
body = t.split(r"\begin{document}")[1].split(r"\bibliographystyle")[0]
body = re.sub(r"(?m)%.*$", "", body)
tells = ["delve", "crucial", "pivotal", "landscape", "tapestry", "underscore", "leverage", "robust", "seamless", "comprehensive",
         "notably", "important to note", "worth noting", "in today", "key role", "serves as", "testament", "moreover", "furthermore",
         "not only", "dramatically", "undoubtedly", "significantly", "validated", "taxonomy", "order of magnitude", "expected direction",
         "worse with data", "precision 1.00", "\u2014", " --- ", "additionally", "importantly", "indeed"]
hits = {w: len(re.findall(re.escape(w), body, flags=re.I)) for w in tells if re.search(re.escape(w), body, flags=re.I)}
print("machine-tell or banned-word hits:", hits or "none")
for kind in ("tab", "fig"):
    labels = re.findall(r"\\label\{(%s:[^}]+)\}" % kind, t)
    refs = set(re.findall(r"\\(?:ref|tableref)\{(%s:[^}]+)\}" % kind, t))
    print(kind, "labels:", labels, "| unreferenced:", [l for l in labels if l not in refs] or "none")
print("pending markers:", re.findall(r"\\pending\{([^}]{0,60})", t))
main_text = body.split(r"\appendix")[0]
words = len(re.sub(r"\\[a-zA-Z]+|[{}$%&~\\]", " ", main_text).split())
print("main-text words (approx):", words)
print("em dashes in source:", t.count("\u2014"), "| '---' in source:", len(re.findall(r"(?<!-)---(?!-)", body)))
